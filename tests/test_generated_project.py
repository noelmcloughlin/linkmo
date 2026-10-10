"""The generated project runs: its own tests pass, and its two doors answer alike.

These tests run the project with LINKMO_TEST_PYTHON, the way its own `just test` would
with uv, and are skipped without it.
"""

from __future__ import annotations

import json
import re
import shutil
import textwrap
from pathlib import Path

import pytest

from tests import helpers as h
from tests.conftest import needs_project_python

pytestmark = needs_project_python


@pytest.fixture(scope="module")
def pets_project(tmp_path_factory, sidecar_template) -> Path:
    """A pets project after its owner has named the classes and filled in the count table."""
    host = h.make_host(tmp_path_factory.mktemp("project"), sidecar_template)
    h.render_linkmo(host)
    project = host / "pets-linkmo"
    (project / "exposure.yaml").write_text(h.PETS_EXPOSURE, encoding="utf-8")
    shutil.copy2(h.PETS / "expected_counts.yaml", project / "tests" / "expected_counts.yaml")
    shutil.copytree(h.PETS / "mappings", project / "mappings")
    for recipe in ("gen-openapi", "gen-ui-config"):
        result = h.run_just(project, recipe)
        assert result.returncode == 0, result.stderr
    return project


def _passed(output: str) -> int:
    match = re.search(r"(\d+) passed", output)
    return int(match.group(1)) if match else 0


def test_the_generated_tests_pass(pets_project):
    result = h.run_just(pets_project, "test", "-q", "-p", "no:cacheprovider")
    assert result.returncode == 0, result.stdout[-3000:] + result.stderr[-2000:]
    cases = len(h.yaml.safe_load((h.PETS / "expected_counts.yaml").read_text(encoding="utf-8"))["cases"])
    # Each case runs once for its count and once for the identity of the two doors.
    assert _passed(result.stdout) >= 2 * cases
    assert " skipped" not in result.stdout.splitlines()[-1]


def test_the_cli_and_the_api_answer_a_filter_identically(pets_project):
    cli = h.run_project(pets_project, "-m", "pets_linkmo", "animal", "--species", "dog", "--vaccinated")
    assert cli.returncode == 0, cli.stderr
    api = h.run_project(
        pets_project,
        "-c",
        textwrap.dedent(
            """
            import json
            from fastapi.testclient import TestClient
            from pets_linkmo.server import app
            with TestClient(app) as client:
                print(json.dumps(client.get("/animal", params={"species": "dog", "vaccinated": "true"}).json()))
            """
        ),
    )
    assert api.returncode == 0, api.stderr
    from_cli, from_api = json.loads(cli.stdout), json.loads(api.stdout)
    assert from_cli == from_api
    assert from_cli["count"] == 4
    assert {item["id"] for item in from_cli["items"]} == {"rex", "biscuit", "max", "duke"}


def test_the_recipes_run_from_the_host_root(pets_project):
    assert (pets_project / "docs" / "openapi.json").is_file()
    contract = json.loads((pets_project / "docs" / "openapi.json").read_text(encoding="utf-8"))
    assert contract["openapi"] == "3.1.0"
    assert set(contract["paths"]) == {"/animal", "/dog", "/cat", "/person", "/shelter", "/summary"}
    entities = json.loads((pets_project / "ui" / "entities.json").read_text(encoding="utf-8"))
    assert [e["key"] for e in entities["endpoints"]] == ["animal", "dog", "cat", "person", "shelter"]
    assert entities["endpoints"][3]["label"] == "People"
    exposure = h.run_just(pets_project, "exposure")
    assert exposure.returncode == 0 and "Dog:" in exposure.stdout


@pytest.mark.skipif(not h.tool("sssom"), reason="sssom is not installed beside LINKMO_TEST_PYTHON")
def test_the_sssom_recipe_validates_each_mapping_file(pets_project, tmp_path):
    good = h.run_just(pets_project, "validate-sssom")
    assert good.returncode == 0, good.stderr
    assert "sssom validate mappings/pets.sssom.tsv" in good.stdout
    broken = tmp_path / "broken"
    broken.mkdir()
    (broken / "broken.sssom.tsv").write_text(
        "# curie_map:\n#   pets: https://example.org/pets/\n# mapping_set_id: https://example.org/x\n"
        "subject_id\tpredicate_id\tobject_id\tmapping_justification\n"
        "pets:Dog\tskos:exactMatch\twd:Q144\tsemapv:ManualMappingCuration\n",
        encoding="utf-8",
    )
    assert h.run_just(pets_project, "validate-sssom", str(broken)).returncode != 0


@pytest.mark.skipif(not (h.tool("datasette") and h.tool("gen-doc")), reason="the browse and docs tools are not installed")
def test_the_browse_build_holds_every_record_in_its_tables(pets_project):
    import sqlite3

    result = h.run_just(pets_project, "build-browse")
    assert result.returncode == 0, result.stderr
    assert "refused" not in result.stdout and "do not exist" not in result.stdout
    database = pets_project / "browse" / "pets.sqlite"
    metadata = h.yaml.safe_load((pets_project / "browse" / "metadata.yaml").read_text(encoding="utf-8"))
    with sqlite3.connect(database) as connection:
        def rows(table: str) -> int:
            return connection.execute(f'select count(*) from "{table}"').fetchone()[0]

        # A table holds its class's records and its subclasses': 15 animals, 24 named things.
        assert (rows("Dog"), rows("Cat"), rows("Animal"), rows("NamedThing")) == (6, 5, 15, 24)
        assert rows("Animal_friends") == 5
        found = connection.execute(
            """select id from "Animal" where rowid in (select rowid from "Animal_fts" where "Animal_fts" match 'whiskers')"""
        ).fetchall()
        assert found == [("whiskers",)]
    tables = metadata["databases"]["pets"]["tables"]
    assert tables["Animal"]["label_column"] == "name"
    assert "species" in tables["Animal"]["facets"]


@pytest.mark.skipif(not h.tool("gen-doc"), reason="gen-doc is not installed beside LINKMO_TEST_PYTHON")
def test_gen_doc_renders_each_class_page_with_its_example(pets_project):
    result = h.run_just(pets_project, "gen-doc")
    assert result.returncode == 0, result.stderr
    assert "validated 5 examples, 0 failed" in result.stdout
    page = (pets_project / "docs" / "elements" / "Dog.md").read_text(encoding="utf-8")
    assert "## Examples" in page and "### Example: Dog-bella" in page


def test_the_derived_exposure_is_the_root_class_collections(tmp_path, sidecar_template):
    host = h.make_host(tmp_path, sidecar_template)
    h.render_linkmo(host)
    project = host / "pets-linkmo"
    derived = h.run_project(project, "-m", "pets_linkmo.exposure")
    assert derived.returncode == 0, derived.stderr
    assert "3 classes, derived from the root class; root class: Registry" in derived.stdout
    assert [line.split(":")[0].strip() for line in derived.stdout.splitlines() if line.startswith("  ") and line.endswith(":")] == [
        "Animal",
        "Person",
        "Shelter",
    ]
    excluding = tmp_path / "exclude.yaml"
    excluding.write_text("generator_args:\n  openapi:\n    exclude:\n      classes: [Shelter]\n", encoding="utf-8")
    env = h.project_env(project) | {"PETS_LINKMO_EXPOSURE": str(excluding)}
    import subprocess

    def count(command: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [h.PROJECT_PYTHON, "-m", "pets_linkmo", command, "--count"], cwd=project, env=env, capture_output=True, text=True
        )

    assert count("animal").stdout.strip() == "15"
    assert count("person").stdout.strip() == "5"
    assert count("shelter").returncode == 2 and "No such command" in count("shelter").stderr
    # The generated tests pass on the derived exposure too, with an empty count table.
    result = h.run_project(project, "-m", "pytest", "-q", "-p", "no:cacheprovider")
    assert result.returncode == 0, result.stdout[-3000:]


SOURCE_EXPOSURE = """\
generator_args:
  openapi:
    expose:
      classes:
        Animal:
          path: /animal
          parameters: [adopted_by]
        Dog:
          path: /dog
        Person:
          path: /person
    overlay:
      components:
        parameters:
          adopted_by:
            in: query
            name: adopted_by
            schema:
              type: string
            description: The person who adopted the animals
"""


def test_a_python_source_answers_with_a_parameter_the_exposure_adds(tmp_path, sidecar_template):
    host = h.make_host(tmp_path, sidecar_template)
    h.render_linkmo(host, {"data_source": "python", "data_object": "pets_linkmo.pets_source:PetsSource"})
    project = host / "pets-linkmo"
    assert 'DATA = _setting("DATA", "pets_linkmo.pets_source:PetsSource")' in (
        project / "src" / "pets_linkmo" / "settings.py"
    ).read_text(encoding="utf-8")
    shutil.copy2(h.PETS / "pets_source.py", project / "src" / "pets_linkmo" / "pets_source.py")
    (project / "exposure.yaml").write_text(SOURCE_EXPOSURE, encoding="utf-8")

    def cli(*args: str) -> dict:
        result = h.run_project(project, "-m", "pets_linkmo", *args)
        assert result.returncode == 0, result.stderr
        return json.loads(result.stdout)

    adopted = cli("animal", "--adopted_by", "aoife")
    assert sorted(item["id"] for item in adopted["items"]) == ["biscuit", "mittens"]
    assert h.run_project(project, "-m", "pets_linkmo", "dog", "--adopted_by", "aoife").returncode == 2
    # The identifier alone fetches one record; with an added parameter the source answers a listing.
    assert cli("animal", "rex")["item"]["name"] == "Rex"
    assert cli("animal", "rex", "--adopted_by", "aoife") == {"items": [], "count": 0, "validation_errors": []}
    api = h.run_project(
        project,
        "-c",
        "import json\nfrom fastapi.testclient import TestClient\nfrom pets_linkmo.server import app\n"
        "print(json.dumps(TestClient(app).get('/animal', params={'adopted_by': 'aoife'}).json()))",
    )
    assert api.returncode == 0, api.stderr
    assert json.loads(api.stdout) == adopted
    # The project's own tests pass with the Python source too.
    result = h.run_project(project, "-m", "pytest", "-q", "-p", "no:cacheprovider")
    assert result.returncode == 0, result.stdout[-3000:]
