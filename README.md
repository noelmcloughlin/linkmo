# linkmo-project-copier

A [copier](https://copier.readthedocs.io) template that turns a LinkML schema and its data into a project with a command line, an HTTP API, a Datasette browse database, schema pages with examples, and tests. The command line and the API are built from the schema each time they start, so a slot added to the schema is a filter at the next start.

It sits beside [linkml-project-copier](https://github.com/linkml/linkml-project-copier) in a host project. The `.linkml/` sidecar owns the schema; this template owns what serves the schema and its data, in one folder at the host root, and writes nothing under `.linkml/`.

## Apply it

From the root of a host that has a `.linkml/` sidecar, with copier 9.4 or later:

```bash
copier copy --trust /path/to/linkmo-project-copier .
```

`--trust` is needed for the one copy step, which generates the sidecar's Python datamodel when it is missing. The answers go to `.copier-answers.linkmo.yml` at the host root, beside the sidecar's own answers.

The project lands in `<slug>-linkmo/`. Its recipes run from the host root the way the sidecar's do:

```bash
just --justfile pets-linkmo/justfile install       # uv sync, once
just --justfile pets-linkmo/justfile cli --help    # the command line
just --justfile pets-linkmo/justfile serve         # the API on http://localhost:8000/docs
just --justfile pets-linkmo/justfile test
```

## The questions

Defaults are read from the sidecar's answers where they exist.

- `sidecar_answers_file`: `.linkml/.copier-answers.yml`, where the other defaults come from.

- `project_slug`: the sidecar's slug, else the host folder's name.

- `linkmo_dir`: `<slug>-linkmo`, the project's folder.

- `schema_path`: `.linkml/src/<slug>/schema/<slug>.yaml`. A schema inside an installed package is written `pkg:<package>/<path>`.

- `datamodel_module`: `<slug>.datamodel.<slug>_pydantic`, the sidecar's gen-pydantic output, or any installed module.

- `root_class`: empty, which means the class the schema marks `tree_root`. Its collection slots decide which classes are exposed until the exposure file names them.

- `exposure_file`: `exposure.yaml`.

- `data_source`: `yaml`, a directory of YAML instance files read through the datamodel, or `python`, an object with `query(class_name, **filters)`.

- `data_path` for `yaml`: `data`, from the host root, or `pkg:<package>/<path>`.

- `data_object` for `python`: `module:attribute`; a class or function found there is called once.

- `cli_framework`: `click`, the only choice in this version.

- `api`: `fastapi`, the only choice in this version.

- `command_name`: the slug with dashes. `python_package`: `<slug>_linkmo`.

## What you get

- One command and one endpoint per exposed class, with one option and one query parameter per slot. An enum slot offers its values; a boolean slot is `--name` or `--no-name`; the identifier fetches one record.

- The same JSON through both: `{"items", "count", "validation_errors"}` for a listing, `{"item"}` for one record. The command line reads the data in the process, or asks the server with `--mode api`.

- FastAPI's OpenAPI 3.1 contract, with the datamodel's model of each class, served at `/openapi.json`, `/docs`, `/redoc` and `/scalar`.

- Recipes: `test`, `cli`, `serve`, `exposure`, `gen-openapi` (publish the contract), `gen-ui-config` (a web UI's entity list), `validate-sssom` (each `mappings/*.sssom.tsv`), `build-browse` and `browse` (SQLite tables from gen-sqltables, served by Datasette), `gen-examples` and `gen-doc` (class pages with an example from the data), `gen-datamodel` and `update-template`.

- Tests: both doors have the same parameters and give the same answers, every slot is a parameter, the count table holds, the published files are current, and the browse database and examples follow the data.

## What is yours

The template creates these once and never overwrites them:

- `exposure.yaml`, which names the exposed classes, their paths and labels, adds parameters a Python source understands, and binds hand-written operations to paths;

- `src/<package>/hand.py`, the hand-written operations, starting with `summary`;

- `tests/expected_counts.yaml`, the questions your data must answer and their counts;

- `tests/test_hand.py`, `project.justfile` and `README.md`.

## Updating

From the host root:

```bash
copier update -a .copier-answers.linkmo.yml --trust
```

Each template updates on its own and runs only its own migrations. This template's destination is the host root, so copier refuses to update it while anything in the host, `.linkml/` included, is uncommitted. The sidecar's update looks only inside `.linkml/`. Without `-a`, copier looks for `.copier-answers.yml` at the root and finds no template.

## Not in this version

- typer for the command line and connexion for the API; each question keeps one choice until another exists.

- A linkml-store database as a data source.

- Publishing the contract with LinkML's gen-openapi, which has no console script yet; `gen-openapi` publishes FastAPI's document meanwhile.

- Path parameters in hand-written operations, and paging in listings.

Working on the template itself is covered in [CONTRIBUTING.md](CONTRIBUTING.md).
