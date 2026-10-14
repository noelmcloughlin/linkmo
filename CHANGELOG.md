# Changelog

All notable changes to this template are documented here. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

A version is a git tag, which copier records in each host's `.copier-answers.linkmo.yml`. The template stays below 1.0.0 until its questions settle, so a breaking change bumps the minor version.

## [Unreleased]

### Changed

- **The template is named linkmo.** The repository moved from `noelmcloughlin/linkmo-project-copier` to `noelmcloughlin/linkmo`; GitHub redirects the old address, so a host's recorded `_src_path` keeps working. The README, the security policy and the test project's name follow.

### Fixed

- **Records of unrelated classes may share an identifier.** The YAML source merged every record with one identifier into one, so a Shelter and a Person both called `galway` became one rejected Person and the Shelter was lost. Two records now merge only when one's class is the other's or an ancestor of it.

## [0.1.0] - 2026-10-11

### Added

- **The linkmo copier template.** It turns a LinkML schema and records from a YAML directory or a Python object into a click command line, a FastAPI API with an OpenAPI 3.1 contract, a Datasette browse build, gen-doc pages with examples, and tests. The tests check that the command line and the API give one answer. The template reads its defaults from the `.linkml/` sidecar's answers and writes nothing under `.linkml/`.
