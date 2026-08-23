# Git hooks for this repository

This repository includes a Git hook at `.githooks/pre-commit` that performs basic syntax checks for endpoint-related Python files before allowing a commit. It targets files under `app/controllers/`, `app/service/`, and `app/main.py`.

To enable the hooks locally (recommended):

1. Make the hook executable:

```bash
chmod +x .githooks/pre-commit
```

2. Tell Git to use the `.githooks` directory for hooks:

```bash
git config core.hooksPath .githooks
```

After these steps, committing will run the syntax checks for staged endpoint files and abort the commit if any syntax errors are found.

The pre-commit hook now also attempts to run the project's test suite using `pytest`. If `pytest` is installed (either as a CLI or importable in the selected Python), the hook will run the tests and abort the commit on failures. If `pytest` is not available the hook will skip tests and allow the commit to proceed.

To enable tests in the hook, install `pytest` in your environment, for example:

```bash
pip install pytest
```

You can also extend the script to run formatting with `black` or linting with `ruff`/`flake8` as desired.

(Edit recorded for testing pre-commit hook.)
