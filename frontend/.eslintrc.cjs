module.exports = {
  root: true,
  env: { browser: true, es2020: true },
  extends: [
    "eslint:recommended",
    "plugin:react/recommended",
    "plugin:react-hooks/recommended",
  ],
  parserOptions: {
    ecmaVersion: "latest",
    sourceType: "module",
    ecmaFeatures: { jsx: true },
  },
  settings: {
    react: { version: "detect" },
  },
  plugins: ["react", "react-hooks"],
  rules: {
    // React 17+ JSX transform: no need to import React in scope
    "react/react-in-jsx-scope": "off",
    "react/prop-types": "off",        // not enforcing prop-types in this project
  },
};
