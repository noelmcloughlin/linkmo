# Contributing

This page is a checklist for work on the template. The code's comments and docstrings give the reasons.

- Run the tests before a pull request. They render the template beside a sidecar made by linkml-project-copier, then run the generated project with a Python that has its packages:

  ```bash
  LINKML_PROJECT_COPIER=/path/to/linkml-project-copier LINKML_PROJECT_COPIER_REF=main \
  LINKMO_TEST_PYTHON=/path/to/venv/bin/python \
  uv run --group dev pytest
  ```

  Without `LINKMO_TEST_PYTHON` the tests that run the project are skipped. Without `LINKML_PROJECT_COPIER` the sidecar is rendered from GitHub.

- A generated file belongs to the template unless `_skip_if_exists` in `copier.yaml` lists it. Keep that list and the README's "What is yours" in agreement.

- Files that need answers end in `.jinja`. Copier copies the justfile as it is, so its own `{{ }}` stay. The justfile reads the package name from `linkmo.env`.

- Generated code reads the schema through `exposure.py` and `schema.py`, never by class or slot name.

- Write comments, docs and messages in plain prose: full sentences, no arrows.

- One commit per change, with a one-line conventional subject under 80 characters, signed off with `git commit -s`. Add a line to the changelog under Unreleased.
