"""Execution Engine: runs DAG runs in background threads.

Flow per run:
  1. Topological sort into waves.
  2. For each wave, execute jobs in parallel (ThreadPoolExecutor).
  3. For each job: optional input validation → main handler → optional output validation.
  4. Persist state after each step.

Handler types (handler_config.type):
  - "script": runs handler_config.command via shell subprocess.
  - "noop":   succeeds immediately (useful for testing).
"""

import json
import logging
import subprocess  # nosec B404 — subprocess use is intentional (script handler)
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.job import Job
from app.models.run import (
    JOB_RUN_STATUS_FAILED,
    JOB_RUN_STATUS_INPUT_VALIDATION,
    JOB_RUN_STATUS_OUTPUT_VALIDATION,
    JOB_RUN_STATUS_PENDING,
    JOB_RUN_STATUS_RUNNING,
    JOB_RUN_STATUS_SKIPPED,
    JOB_RUN_STATUS_SUCCESS,
    RUN_STATUS_FAILED,
    RUN_STATUS_RUNNING,
    RUN_STATUS_SUCCESS,
)
from app.repositories.dag_repository import DAGRepository
from app.repositories.job_repository import JobRepository
from app.repositories.job_run_state_repository import JobRunStateRepository
from app.repositories.run_repository import RunRepository
from app.services.dag_service import topological_waves

logger = logging.getLogger(__name__)

# Per-job concurrency lock: prevents concurrent runs of the same job when concurrency_enabled=False.
_job_locks: dict[str, threading.Lock] = {}
_job_locks_mutex = threading.Lock()


def _get_job_lock(job_id: str) -> threading.Lock:
    with _job_locks_mutex:
        if job_id not in _job_locks:
            _job_locks[job_id] = threading.Lock()
        return _job_locks[job_id]


def _now() -> datetime:
    return datetime.now(tz=UTC)


def _run_command(command: str, timeout: int = 300) -> tuple[bool, str]:
    """Run a shell command. Returns (success, output/error)."""
    try:
        result = subprocess.run(
            command,
            shell=True,  # nosec B602 — command strings are user-configured job definitions, not interpolated user input
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = result.stdout + result.stderr
        return result.returncode == 0, output
    except subprocess.TimeoutExpired:
        return False, f"Command timed out after {timeout}s"
    except Exception as exc:
        return False, str(exc)


def _run_container(
    image: str,
    command: str,
    timeout: int = 300,
    environment: dict | None = None,
    volumes: list | None = None,
) -> tuple[bool, str]:
    """Run a command inside a Docker container. Returns (success, logs)."""
    try:
        import docker  # deferred: backend starts fine without SDK
        from docker.errors import ImageNotFound
    except ImportError:
        return (
            False,
            "docker SDK not installed; add 'docker>=7.0.0' to requirements.txt",
        )

    from app.config import get_settings

    settings = get_settings()

    kwargs = {}
    if settings.docker_host:
        kwargs["base_url"] = settings.docker_host

    try:
        client = docker.DockerClient(**kwargs) if kwargs else docker.from_env()
    except Exception as exc:
        return False, f"Cannot connect to Docker daemon: {exc}"

    # Build volumes dict from "host:container[:mode]" strings
    volume_binds: dict = {}
    for vol in volumes or []:
        parts = str(vol).split(":")
        if len(parts) >= 2:
            host_path, container_path = parts[0], parts[1]
            mode = parts[2] if len(parts) >= 3 else "rw"
            volume_binds[host_path] = {"bind": container_path, "mode": mode}

    container = None
    try:
        try:
            client.images.get(image)
        except ImageNotFound:
            client.images.pull(image)

        container = client.containers.run(
            image,
            command=command,
            environment=environment or {},
            volumes=volume_binds or None,
            detach=True,
        )
        result = container.wait(timeout=timeout)
        logs = container.logs(stdout=True, stderr=True).decode("utf-8", errors="replace")
        exit_code = result.get("StatusCode", 1)
        return exit_code == 0, logs
    except Exception as exc:
        return False, str(exc)
    finally:
        if container is not None:
            try:
                container.remove(force=True)
            except Exception:  # nosec B110 — best-effort container cleanup; failure is non-fatal
                pass


def _execute_handler(handler_config: dict) -> tuple[bool, str]:
    """Execute a job handler. Returns (success, log_output)."""
    handler_type = handler_config.get("type", "noop")

    if handler_type == "noop":
        return True, "noop: success"

    if handler_type == "script":
        command = handler_config.get("command", "")
        if not command:
            return False, "handler_config.command is required for type=script"
        timeout = int(handler_config.get("timeout", 300))
        return _run_command(command, timeout)

    if handler_type == "container":
        image = handler_config.get("image", "")
        command = handler_config.get("command", "")
        if not image:
            return False, "handler_config.image is required for type=container"
        if not command:
            return False, "handler_config.command is required for type=container"
        timeout = int(handler_config.get("timeout", 300))
        env = handler_config.get("environment", {})
        vols = handler_config.get("volumes", [])
        return _run_container(image, command, timeout, env, vols)

    return False, f"Unknown handler type: {handler_type}"


def _execute_job(run_id: str, job: Job, db: Session) -> bool:
    """Execute one job (input validation → handler → output validation). Returns success."""
    state_repo = JobRunStateRepository(db)
    run_repo = RunRepository(db)

    # Check if run was cancelled
    run = run_repo.get(run_id)
    if run and run.status == "cancelled":
        state = state_repo.get_by_run_and_job(run_id, job.id)
        if state:
            state.status = JOB_RUN_STATUS_SKIPPED
            db.commit()
        return False

    state = state_repo.get_by_run_and_job(run_id, job.id)
    if not state:
        return False

    log_parts: list[str] = []

    # ── Input validation ──
    if job.input_validation_enabled and job.validator_config:
        state.status = JOB_RUN_STATUS_INPUT_VALIDATION
        state.started_at = _now()
        db.commit()

        try:
            vcfg = (
                json.loads(job.validator_config)
                if isinstance(job.validator_config, str)
                else job.validator_config
            )
            ok, output = _execute_handler(vcfg)
        except Exception as exc:
            ok, output = False, str(exc)

        log_parts.append(f"[input_validation]\n{output}")

        if not ok:
            state.status = JOB_RUN_STATUS_FAILED
            state.error_message = f"Input validation failed: {output[:2000]}"
            state.logs = "\n\n".join(log_parts)
            state.finished_at = _now()
            db.commit()
            return False

    # ── Main handler ──
    state.status = JOB_RUN_STATUS_RUNNING
    if state.started_at is None:
        state.started_at = _now()
    db.commit()

    try:
        hcfg = (
            json.loads(job.handler_config)
            if isinstance(job.handler_config, str)
            else job.handler_config
        )
        ok, output = _execute_handler(hcfg)
    except Exception as exc:
        ok, output = False, str(exc)

    log_parts.append(f"[handler]\n{output}")

    if not ok:
        state.status = JOB_RUN_STATUS_FAILED
        state.error_message = output[:2000]
        state.logs = "\n\n".join(log_parts)
        state.finished_at = _now()
        db.commit()
        return False

    # ── Output validation ──
    if job.output_validation_enabled and job.validator_config:
        state.status = JOB_RUN_STATUS_OUTPUT_VALIDATION
        db.commit()

        try:
            vcfg = (
                json.loads(job.validator_config)
                if isinstance(job.validator_config, str)
                else job.validator_config
            )
            ok, output = _execute_handler(vcfg)
        except Exception as exc:
            ok, output = False, str(exc)

        log_parts.append(f"[output_validation]\n{output}")

        if not ok:
            state.status = JOB_RUN_STATUS_FAILED
            state.error_message = f"Output validation failed: {output[:2000]}"
            state.logs = "\n\n".join(log_parts)
            state.finished_at = _now()
            db.commit()
            return False

    state.logs = "\n\n".join(log_parts)
    state.status = JOB_RUN_STATUS_SUCCESS
    state.finished_at = _now()
    db.commit()
    return True


def _execute_job_with_lock(run_id: str, job: Job, db: Session) -> tuple[str, bool]:
    """Wrapper that respects the job's concurrency_enabled flag."""
    if not job.concurrency_enabled:
        lock = _get_job_lock(job.id)
        with lock:
            success = _execute_job(run_id, job, db)
    else:
        success = _execute_job(run_id, job, db)
    return job.id, success


def _run_dag(run_id: str) -> None:
    """Background thread entry point: execute a DAG run from start to finish."""
    db: Session = SessionLocal()
    try:
        run_repo = RunRepository(db)
        dag_repo = DAGRepository(db)
        job_repo = JobRepository(db)
        state_repo = JobRunStateRepository(db)

        run = run_repo.get(run_id)
        if not run:
            logger.error("Run %s not found", run_id)
            return

        if run.status == "cancelled":
            return

        dag = dag_repo.get_with_edges(run.dag_id)
        if not dag:
            logger.error("DAG %s not found for run %s", run.dag_id, run_id)
            run.status = RUN_STATUS_FAILED
            db.commit()
            return

        run.status = RUN_STATUS_RUNNING
        db.commit()

        edges = [(e.from_job_id, e.to_job_id) for e in dag.edges]
        job_ids = list({j for pair in edges for j in pair})

        # Also include jobs that have states but no edges (isolated nodes)
        for state in state_repo.list_by_run(run_id):
            if state.job_id not in job_ids:
                job_ids.append(state.job_id)

        waves = topological_waves(job_ids, edges)
        if not waves and job_ids:
            # No edges at all — all jobs are independent, run in one wave
            waves = [job_ids]

        # Load job objects
        jobs_by_id: dict[str, Job] = {j.id: j for j in job_repo.list_by_ids(job_ids)}

        any_failed = False

        for wave in waves:
            # Check for cancellation before each wave
            db.expire(run)
            run = run_repo.get(run_id)
            if run.status == "cancelled":
                # Mark remaining pending jobs as skipped
                for state in state_repo.list_by_run(run_id):
                    if state.status == JOB_RUN_STATUS_PENDING:
                        state.status = JOB_RUN_STATUS_SKIPPED
                db.commit()
                return

            if any_failed:
                # Skip downstream jobs
                for job_id in wave:
                    state = state_repo.get_by_run_and_job(run_id, job_id)
                    if state and state.status == JOB_RUN_STATUS_PENDING:
                        state.status = JOB_RUN_STATUS_SKIPPED
                db.commit()
                continue

            with ThreadPoolExecutor(max_workers=len(wave) or 1) as executor:
                futures = {
                    executor.submit(_execute_job_with_lock, run_id, jobs_by_id[jid], db): jid
                    for jid in wave
                    if jid in jobs_by_id
                }
                for future in as_completed(futures):
                    try:
                        _job_id, success = future.result()
                        if not success:
                            any_failed = True
                    except Exception as exc:
                        any_failed = True
                        logger.exception("Unhandled error in job execution: %s", exc)

        run = run_repo.get(run_id)
        if run and run.status != "cancelled":
            run.status = RUN_STATUS_FAILED if any_failed else RUN_STATUS_SUCCESS
            db.commit()

    except Exception:
        logger.exception("Fatal error in run %s", run_id)
        try:
            run = RunRepository(db).get(run_id)
            if run:
                run.status = RUN_STATUS_FAILED
                db.commit()
        except Exception:  # nosec B110 — best-effort DB status update; already in fatal-error handler
            pass
    finally:
        db.close()


class ExecutionEngine:
    """Dispatch DAG runs to background threads."""

    def trigger(self, run_id: str) -> None:
        """Start executing a run asynchronously."""
        t = threading.Thread(target=_run_dag, args=(run_id,), daemon=True)
        t.start()
        logger.info("Triggered run %s in thread %s", run_id, t.name)
