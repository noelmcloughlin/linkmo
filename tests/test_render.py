"""The template renders beside a .linkml/ sidecar, reads its answers, and stays out of it."""

from __future__ import annotations

import shutil
import warnings

import yaml
from copier.errors import MissingFileWarning

from tests import helpers as h


def test_the_answers_file_sits_at_the_host_root_beside_the_sidecars(pets_host, sidecar_template):
    host, _ = pets_host
    linkmo = h.answers(host)
    sidecar = h.answers(host, ".linkml/.copier-answers.yml")
    assert linkmo["_src_path"] and linkmo["_commit"]
    assert linkmo["sidecar_answers_file"] == ".linkml/.copier-answers.yml"
    # Each answers file names its own template, so the two updates never mix them up.
    assert sidecar["_commit"] and sidecar["_src_path"] == str(sidecar_template)
    assert linkmo["_src_path"] != sidecar["_src_path"]


def test_external_data_reads_the_sidecar_answers_from_the_host_root(pets_host):
    host, caught = pets_host
    recorded = h.answers(host)
    # The host folder is called host, so a slug of pets can only have come from the sidecar.
    assert host.name == "host"
    assert recorded["project_slug"] == h.SIDECAR_ANSWERS["project_slug"] == "pets"
    assert recorded["schema_path"] == ".linkml/src/pets/schema/pets.yaml"
    assert recorded["datamodel_module"] == "pets.datamodel.pets_pydantic"
    assert recorded["linkmo_dir"] == "pets-linkmo"
    assert recorded["python_package"] == "pets_linkmo"
    assert recorded["command_name"] == "pets"
    assert not [w for w in caught if issubclass(w.category, MissingFileWarning)]


def test_external_data_follows_a_sidecar_answers_file_elsewhere(tmp_path):
    host = h.make_host(tmp_path, None, name="elsewhere")
    (host / "schema-tools").mkdir()
    (host / "schema-tools" / "answers.yml").write_text(
        yaml.safe_dump({"project_slug": "zoo", "_commit": "v0.5.0"}), encoding="utf-8"
    )
    h.render_linkmo(host, {"sidecar_answers_file": "schema-tools/answers.yml"})
    recorded = h.answers(host)
    assert recorded["project_slug"] == "zoo"
    assert recorded["schema_path"] == "schema-tools/src/zoo/schema/zoo.yaml"
    assert (host / "zoo-linkmo" / "src" / "zoo_linkmo" / "settings.py").is_file()


def test_without_a_sidecar_the_defaults_fall_back_to_the_host(tmp_path):
    host = h.make_host(tmp_path, None, name="My Host")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        h.render_linkmo(host)
    missing = [str(w.message) for w in caught if issubclass(w.category, MissingFileWarning)]
    assert any(".linkml/.copier-answers.yml" in message for message in missing)
    recorded = h.answers(host)
    assert recorded["project_slug"] == "my_host"
    assert recorded["schema_path"] == "schema/my_host.yaml"
    assert (host / "my-host-linkmo" / "justfile").is_file()


def test_copying_into_the_current_folder_names_the_slug_after_it(tmp_path, monkeypatch):
    host = h.make_host(tmp_path, None, name="Zoo-Host")
    monkeypatch.chdir(host)
    from copier import run_copy

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        run_copy(str(h.TEMPLATE_ROOT), ".", data={}, defaults=True, unsafe=True, vcs_ref="HEAD", quiet=True)
    assert h.answers(host)["project_slug"] == "zoo_host"


def test_nothing_under_the_sidecar_changes_but_its_generated_datamodel(pets_host):
    host, _ = pets_host
    assert h.git(host, "diff", "--name-only", "HEAD", "--", ".linkml") == ""
    untracked = set(h.git(host, "ls-files", "--others", "--exclude-standard", "--", ".linkml").split())
    if h.PROJECT_PYTHON:
        assert untracked == {
            ".linkml/src/pets/datamodel/pets_pydantic.py",
            ".linkml/src/pets/datamodel/pets.py",
        }
    else:
        assert untracked <= {
            ".linkml/src/pets/datamodel/pets_pydantic.py",
            ".linkml/src/pets/datamodel/pets.py",
        }


def test_the_copy_step_leaves_an_existing_datamodel_alone(tmp_path, sidecar_template):
    host = h.make_host(tmp_path, sidecar_template)
    datamodel = host / ".linkml" / "src" / "pets" / "datamodel"
    for name in ("pets.py", "pets_pydantic.py"):
        (datamodel / name).write_text("# the sidecar's own copy\n", encoding="utf-8")
    h.commit_all(host, "the sidecar generated its datamodel")
    h.render_linkmo(host)
    for name in ("pets.py", "pets_pydantic.py"):
        assert (datamodel / name).read_text(encoding="utf-8") == "# the sidecar's own copy\n"


def test_the_project_files(pets_host):
    host, _ = pets_host
    project = host / "pets-linkmo"
    package = project / "src" / "pets_linkmo"
    for name in ("settings.py", "schema.py", "datamodel.py", "exposure.py", "sources.py", "handlers.py",
                 "cli.py", "api_kernel.py", "server.py", "output.py", "hand.py"):
        assert (package / name).is_file(), name
    for name in ("exposure.yaml", "justfile", "project.justfile", "linkmo.env", "pyproject.toml", "README.md",
                 "scripts/gen_datamodel.py", "scripts/export_openapi.py", "scripts/gen_ui_config.py",
                 "tests/expected_counts.yaml", "tests/test_cli_api_identity.py", "tests/test_counts.py"):
        assert (project / name).is_file(), name
    # The justfile is copied as it is, so its own {{ }} stay.
    assert "{{ python }} -m pytest" in (project / "justfile").read_text(encoding="utf-8")
    assert "LINKMO_PACKAGE=pets_linkmo" in (project / "linkmo.env").read_text(encoding="utf-8")
    settings = (package / "settings.py").read_text(encoding="utf-8")
    assert 'ENV_PREFIX = "PETS_LINKMO"' in settings
    assert '"SCHEMA", ".linkml/src/pets/schema/pets.yaml"' in settings
    # Nothing was written outside the project folder but the answers file.
    tracked = set(h.git(host, "ls-files").split())
    written = set(h.git(host, "ls-files", "--others", "--exclude-standard").split()) - tracked
    assert {p.split("/", 1)[0] for p in written} <= {".copier-answers.linkmo.yml", "pets-linkmo", ".linkml"}


def test_the_pyproject_leaves_linkml_out_and_names_the_command(pets_host):
    host, _ = pets_host
    import tomllib

    pyproject = tomllib.loads((host / "pets-linkmo" / "pyproject.toml").read_text(encoding="utf-8"))
    names = [dep.split(">")[0].split("<")[0].split("=")[0].strip() for dep in pyproject["project"]["dependencies"]]
    assert "linkml-runtime" in names and "linkml" not in names and "chardet" not in names
    assert pyproject["project"]["scripts"] == {"pets": "pets_linkmo.cli:main"}


def test_project_owned_files_survive_a_second_copy(tmp_path, sidecar_template):
    host = h.make_host(tmp_path, sidecar_template)
    h.render_linkmo(host)
    project = host / "pets-linkmo"
    owned = ["exposure.yaml", "README.md", "project.justfile", "src/pets_linkmo/hand.py", "tests/expected_counts.yaml"]
    for name in owned:
        with open(project / name, "a", encoding="utf-8") as handle:
            handle.write("\n# changed by the project\n")
    with open(project / "src" / "pets_linkmo" / "cli.py", "a", encoding="utf-8") as handle:
        handle.write("\n# changed by hand\n")
    h.commit_all(host, "the project's own changes")
    from copier import run_copy

    with h.task_env():
        run_copy(str(h.TEMPLATE_ROOT), host, data={}, defaults=True, overwrite=True, unsafe=True, vcs_ref="HEAD", quiet=True)
    for name in owned:
        assert (project / name).read_text(encoding="utf-8").endswith("# changed by the project\n"), name
    assert "# changed by hand" not in (project / "src" / "pets_linkmo" / "cli.py").read_text(encoding="utf-8")


def test_the_template_leaves_its_own_files_out_of_the_project(pets_host):
    host, _ = pets_host
    for name in ("copier.yaml", "CHANGELOG.md", "CONTRIBUTING.md", "tests/helpers.py"):
        assert not (host / name).exists(), name
    shutil.rmtree(host / "pets-linkmo" / ".pytest_cache", ignore_errors=True)
