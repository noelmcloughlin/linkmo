# linkmo

linkmo is a [copier](https://copier.readthedocs.io) template that turns a LinkML schema and its data into a project with a command line, an HTTP API, a Datasette browse database, schema pages with examples, and tests. The command line and the API are built from the schema each time they start, so a slot added to the schema is a filter at the next start.

It sits beside [linkml-project-copier](https://github.com/linkml/linkml-project-copier) in a host project. The `.linkml/` sidecar owns the schema. This template owns what serves the schema and its data. It keeps that in one folder at the host root, and writes nothing under `.linkml/`.

## Apply it

From the root of a host that has a `.linkml/` sidecar, with copier 9.4 or later:

```bash
copier copy --trust gh:noelmcloughlin/linkmo .
```

Copier takes the latest release; `--vcs-ref v0.1.0` pins one. It needs `--trust` for the one copy step, which generates the sidecar's Python datamodel when it is missing. The answers go to `.copier-answers.linkmo.yml` at the host root, beside the sidecar's answers.

Copier writes the project to `<slug>-linkmo/`. Its recipes run from the host root the way the sidecar's do:

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

- `data_object` for `python`: `module:attribute`. A class or function found there is called once. The host root is on the path last, so the object may live in the host's own code.

- `requirements` when a path starts with `pkg:`: the package's name with dashes, such as `[ai-atlas-nexus]`. The list joins the project's dependencies. Answer `[]` to run the project on an environment that has the package already, with `LINKMO_PYTHON` set to its Python.

- `cli_framework`: `click`, the only choice in this version.

- `api`: `fastapi`, the only choice in this version.

- `command_name`: the slug with dashes.

- `python_package`: `<slug>_linkmo`.

- `env_prefix`: the package's name in capitals, which starts each setting's environment variable, as in `PETS_LINKMO_DATA`. Choose another when the host already has variables that start with it.

- `openapi_file` and `entities_file`: `<slug>-linkmo/docs/openapi.json` and `<slug>-linkmo/ui/entities.json`, from the host root, where `gen-openapi` and `gen-ui-config` write and the tests look.

## What you get

- One command and one endpoint per exposed class, with one option and one query parameter per slot. An enum slot offers its values. A boolean slot is `--name` or `--no-name`. The identifier fetches one record.

- The same JSON through both: `{"items", "count", "validation_errors"}` for a listing, `{"item"}` for one record. The command line reads the data in the process, or asks the server with `--mode api`, and indents the JSON on a terminal.

- FastAPI's OpenAPI 3.1 contract, with the datamodel's model of each class, served at `/openapi.json`, `/docs`, `/redoc` and `/scalar`.

- Recipes:

  - `test`, `cli`, `serve` and `exposure`;

  - `gen-openapi` (publish the contract) and `gen-ui-config` (a web UI's entity list);

  - `validate-sssom` (each `mappings/*.sssom.tsv`);

  - `build-browse` and `browse` (SQLite tables from gen-sqltables, served by Datasette; `--param` passes an added parameter to each question);

  - `gen-examples` and `gen-doc` (class pages with an example from the data);

  - `gen-datamodel` and `update-template`.

- Tests: the command line and the API have the same parameters and give the same answers, every slot is a parameter, the count table holds, the published files are current, and the browse database and examples follow the data.

## What is yours

The template creates these once and never overwrites them:

- `exposure.yaml`, which names the exposed classes, their paths and labels, adds parameters a Python source understands, and binds hand-written operations to paths. An added parameter asks a question of its own, so with the identifier the answer is a listing, unless its definition says `x-linkmo-filter: true`. A hand operation's parameter marked `x-linkmo-argument: true` is its command's argument;

- `src/<package>/hand.py`, the hand-written operations, starting with `summary`;

- `tests/expected_counts.yaml`, the questions your data must answer and their counts;

- `tests/test_hand.py`, `project.justfile` and `README.md`.

## Updating

From the host root:

```bash
copier update -a .copier-answers.linkmo.yml --trust
```

Each template is updated separately and runs only its own migrations. Copier refuses to update this template while anything in the host, `.linkml/` included, is uncommitted, because the template's destination is the host root. The sidecar's update looks only inside `.linkml/`. Without `-a`, copier looks for `.copier-answers.yml` at the root and finds no template.

## Not in this version

- typer for the command line and connexion for the API. Each question keeps one choice until another exists.

- A linkml-store database as a data source.

- Publishing the contract with LinkML's gen-openapi, which has no console script yet. Until it has one, the `gen-openapi` recipe publishes FastAPI's document.

- Path parameters in hand-written operations, and paging in listings.

[CONTRIBUTING.md](CONTRIBUTING.md) covers work on the template itself, and [SECURITY.md](SECURITY.md) how to report a vulnerability.
