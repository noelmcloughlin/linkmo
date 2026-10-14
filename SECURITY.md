# Security policy

*This file is a policy, not a threat model. It says how to report a vulnerability, what runs when you apply the template, what a generated project exposes, and what holds each surface of this repository's automation.*

## Reporting a vulnerability

Use GitHub's [private vulnerability reporting](https://github.com/noelmcloughlin/linkmo/security/advisories/new), not a public issue or a pull request. Say which file is affected, how it is exploitable, and whether it reaches a generated project or only this repository's automation. One person maintains this template: expect a first reply in days, not hours, and no bounty.

## Supported versions

Only the latest release receives fixes. A security fix ships as a patch release, is noted in [CHANGELOG.md](CHANGELOG.md), and reaches a host through `copier update`.

## What runs when you apply the template

Copier needs `--trust` for one task, which runs only on the first copy. It runs `scripts/gen_datamodel.py --if-missing`, which runs gen-pydantic and gen-python over the schema when the sidecar's datamodel is missing, and installs nothing. It finds them through `LINKMO_LINKML_BIN`, then the sidecar's `.venv`, then `PATH`. [copier.yaml](copier.yaml) says when the task runs.

## What a generated project exposes

- The API has no authentication. `just serve` binds uvicorn to 127.0.0.1, and CORS admits only local development origins until `<PACKAGE>_CORS_ORIGINS` widens it, `<PACKAGE>` being the Python package's name in capitals.
- The class endpoints only read. A hand-written operation does what its owner writes, through any method its `exposure.yaml` entry binds.
- The project imports what its answers name: the datamodel module and, for a `python` data source, the object `data_object` names. Both are the host's own code.
- The `/scalar` page loads Scalar's script from jsDelivr at its latest version, without subresource integrity. `/docs` and `/redoc` are FastAPI's own pages.

## What executes here

| Surface | What holds it |
| --- | --- |
| `test.yaml`, on every pull request, every push to `main` and weekly: renders the template and runs the generated project | A read-only token with `persist-credentials: false`. `uv sync --locked` installs only what `uv.lock` pins. |
| `links.yaml`, on every pull request, every push to `main` and weekly: checks the links in the Markdown | A read-only token with `persist-credentials: false`. GitHub's API is read with the job's own token. |
| `semantic-release.yml`, which pushes a changelog commit and a tag to `main` and publishes the release | Runs only on a push to `main`, in the `release` Environment, and installs its pinned tools with `--ignore-scripts`. |

Every workflow declares `permissions: {}` at the top, pins its actions to commit SHAs that Dependabot keeps current, and runs harden-runner in audit mode. Three things are repository settings, not files, and **are not yet in force here**: required reviewers on the `release` Environment, private vulnerability reporting, and a rule blocking deletion and force-pushes on `main`. Until the first is set, a qualifying merge releases with no human step.

## Not covered

- linkml-project-copier and the `.linkml/` sidecar it makes: report to [linkml-project-copier](https://github.com/linkml/linkml-project-copier/issues).
- Copier, LinkML, FastAPI and Datasette: report to each project.
- The files a generated project owns once they exist (the exposure file, `hand.py`, the count table): their owner's.
