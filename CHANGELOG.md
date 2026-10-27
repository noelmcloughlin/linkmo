# Changelog

All notable changes to this template are documented here. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

A version is a git tag, which copier records in each host's `.copier-answers.linkmo.yml`. The template stays below 1.0.0 until its questions settle, so a breaking change bumps the minor version.

## [Unreleased]

### Added

- **The `env_prefix` question.** A host whose own variables start with the package's name in capitals chooses another prefix for the project's settings.
- **The `openapi_file` and `entities_file` questions.** `gen-openapi`, `gen-ui-config` and the published-file tests use these paths, so a host can publish outside the project folder.
- **`x-linkmo-filter: true` on an added parameter.** Such a parameter only chooses records, so with the identifier the answer stays one record.
- **`x-linkmo-argument: true` on a hand operation's query parameter.** The command line takes it as the command's argument rather than an option.
- **`build-browse --param name=value`.** The data source is asked with that parameter, and `--data-dir` keeps the database apart; `browse` takes the folder to serve.

### Changed

- **JSON is indented on a terminal**, and stays one line in a pipe.

### Fixed

- **The host root is on the path, last.** A Python data source and `hand.py` can import the host's own modules.
- **Local mode reports a hand operation's `HTTPException`** as the API does, in place of a traceback.
- **The README names a sidecar only when one was found.**

## [0.2.0] - 2026-10-27

### Added

- **A `pkg:` path's package is a dependency.** The `requirements` question, asked when the schema or data path starts with `pkg:`, guesses the distribution from the package's name and adds it to the generated dependencies. Answer `[]` to use an environment that has it through `LINKMO_PYTHON`, whose recipes now put `src/` on the path.

### Fixed

- **Default labels keep acronyms and leave mass nouns alone.** A word that the class's title, aliases or description writes only in capitals keeps them, so `AiTask` is "AI Tasks", and `Documentation` takes no plural.

## [0.1.3] - 2026-10-27

### Added

- **A link check.** `links.yaml` runs lychee over the Markdown on each pull request, each push to main and weekly, handling github.com as knowledge-trust-ladder does.

### Security

- **The test lock pins certifi 2026.10.23.** Older bundles trust an emSign root whose intermediate keys were compromised ([GHSA-6q48-6c7w-9gw2](https://github.com/advisories/GHSA-6q48-6c7w-9gw2)); a generated project resolves its own certifi.

## [0.1.2] - 2026-10-14

### Fixed

- **A hyphenated slug renders.** The datamodel module default writes the hyphen as an underscore, so `copier copy --defaults` no longer fails its own validator.
- **The project folder must end in a letter or digit.** Its name is the generated distribution's name, and a trailing `.`, `_` or `-` is not a valid package name, so `uv sync` refused it.

## [0.1.1] - 2026-10-14

### Changed

- **The template is named linkmo.** The repository moved from `noelmcloughlin/linkmo-project-copier` to `noelmcloughlin/linkmo`; GitHub redirects the old address, so a host's recorded `_src_path` keeps working. The README, the security policy and the test project's name follow.

### Fixed

- **Records of unrelated classes may share an identifier.** The YAML source merged every record with one identifier into one, so a Shelter and a Person both called `galway` became one rejected Person and the Shelter was lost. Two records now merge only when one's class is the other's or an ancestor of it.
- **A data file may hold a list of root instances.** Each item's collections are read, where before each item became an empty root record and its records were lost.
- **A designator naming a class the schema lacks is reported on the listing.** The error was keyed under the unknown name, so no listing showed it.

## [0.1.0] - 2026-10-11

### Added

- **The linkmo copier template.** It turns a LinkML schema and records from a YAML directory or a Python object into a click command line, a FastAPI API with an OpenAPI 3.1 contract, a Datasette browse build, gen-doc pages with examples, and tests. The tests check that the command line and the API give one answer. The template reads its defaults from the `.linkml/` sidecar's answers and writes nothing under `.linkml/`.
