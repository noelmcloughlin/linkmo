# Contributing

This page is a checklist for work on the template. The code's comments and docstrings give the reasons.

- Run the tests before a pull request. They render the template beside a sidecar made by linkml-project-copier, then run the generated project. The `project` dependency group installs the generated project's packages, so this environment's Python can run it:

  ```bash
  uv sync --all-groups
  LINKMO_TEST_PYTHON="$PWD/.venv/bin/python" uv run pytest
  ```

  Without `LINKMO_TEST_PYTHON` the tests that run the project are skipped. The sidecar comes from GitHub at `LINKML_PROJECT_COPIER_REF`, a branch or a tag, `main` by default, or from the clone that `LINKML_PROJECT_COPIER` names. CI tests v0.5.0, the release the linkml-sidecar skill installs, and `main`.

- A generated file belongs to the template unless `_skip_if_exists` in `copier.yaml` lists it. Keep that list and the README's "What is yours" in agreement.

- Files that need answers end in `.jinja`. Copier copies the justfile as it is, so its own `{{ }}` stay. The justfile reads the package name from `linkmo.env`.

- Generated code reads the schema through `exposure.py` and `schema.py`, never by class or slot name.

- A change to the generated project's dependencies changes the `project` group in `pyproject.toml` too. Commit `uv.lock` with any change to `pyproject.toml`, because CI installs with `uv sync --locked`.

- Actions are pinned to commit SHAs, with the version in a trailing comment. Dependabot bumps them.

- Write comments, docs and messages in plain prose: full sentences, no arrows.

- One commit per change, with a one-line conventional subject under 80 characters, signed off with `git commit -s`. Add a line to the changelog under Unreleased.

## Releasing

- Only `feat:`, `fix:` and `security:` commits, and breaking changes, cut a release. A pull request that would release needs its type in its title too, because a squash merge takes its subject from the title.

- On a merge to `main`, [semantic-release.yml](.github/workflows/semantic-release.yml) dates the Unreleased section, commits `CHANGELOG.md`, tags `vX.Y.Z` and publishes the GitHub Release with the same text. It refuses an empty section. No file carries the version: copier reads the tag.

- The release job runs in the `release` Environment. Give it required reviewers in Settings, Environments, or every qualifying merge releases unattended.

- Below 1.0.0 a breaking change bumps the minor version, by a rule in `.releaserc.json`. Reaching 1.0.0 means removing that rule in a pull request of its own.
