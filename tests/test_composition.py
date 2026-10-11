"""Two templates in one host: linkml-project-copier in .linkml/ and linkmo at the root.

Copier has no template inheritance. Several templates share a project through separate
answers files, and each is updated on its own. These tests record what copier 9 does when
both templates' `copier update` run in one host and both declare `_migrations`. Each
template gets a new tagged version with one migration that writes a line to a log.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from copier import run_update
from copier.errors import UserMessageError

from tests import helpers as h

pytestmark = pytest.mark.slow

# The sidecar's newer version in these tests. The mirror carries linkml-project-copier's
# real tags, so the test's own release takes a version no real release will reach soon.
SIDECAR_NEXT = "v99.0.0"


@pytest.fixture
def two_templates(tmp_path, sidecar_template):
    """A host with the sidecar at the ref under test and linkmo at v0.1.0, and a newer
    version of each template, SIDECAR_NEXT and v0.2.0, that declares a migration."""
    lpc = tmp_path / "lpc-work"
    subprocess.run(["git", "clone", "-q", str(sidecar_template), str(lpc)], check=True)
    for key, value in (("user.email", "test@example.org"), ("user.name", "Test"), ("commit.gpgsign", "false"), ("tag.gpgsign", "false")):
        h.git(lpc, "config", key, value)
    linkmo = h.snapshot_template(tmp_path / "linkmo-template", tag="v0.1.0")
    host = h.make_host(tmp_path, lpc)
    h.render_linkmo(host, src=linkmo, vcs_ref="v0.1.0")
    h.commit_all(host, "linkmo v0.1.0")

    line = 'echo "{name} $PWD $STAGE $VERSION_FROM $VERSION_TO" >> "$MIGRATION_LOG"'
    with open(lpc / "copier.yaml", "a", encoding="utf-8") as handle:
        handle.write(f"  - version: {SIDECAR_NEXT}\n    command: {line.format(name='sidecar')}\n")
    h.commit_all(lpc, "a migration")
    h.git(lpc, "tag", SIDECAR_NEXT)
    with open(linkmo / "copier.yaml", "a", encoding="utf-8") as handle:
        handle.write(f"\n_migrations:\n  - version: v0.2.0\n    command: {line.format(name='linkmo')}\n")
    with open(linkmo / "template" / "{{ linkmo_dir }}" / "justfile", "a", encoding="utf-8") as handle:
        handle.write("\n# added in v0.2.0\n")
    h.commit_all(linkmo, "v0.2.0")
    h.git(linkmo, "tag", "v0.2.0")

    # The project's own line in a file it owns, and the sidecar's datamodel removed, so
    # that a copy task run by mistake during an update would show.
    with open(host / "pets-linkmo" / "exposure.yaml", "a", encoding="utf-8") as handle:
        handle.write("# the project's own line\n")
    for name in ("pets.py", "pets_pydantic.py"):
        (host / ".linkml" / "src" / "pets" / "datamodel" / name).unlink(missing_ok=True)
    h.commit_all(host, "the project's changes")
    return host, tmp_path / "migrations.log"


def _log(path: Path) -> list[list[str]]:
    return [line.split() for line in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []


def test_each_update_runs_only_its_own_migrations_in_its_own_folder(two_templates):
    host, log = two_templates
    with h.task_env(MIGRATION_LOG=str(log)):
        h.update_sidecar(host, SIDECAR_NEXT)
        sidecar_entries = _log(log)
        assert [entry[:3] for entry in sidecar_entries] == [["sidecar", str(host / ".linkml"), "after"]]
        assert sidecar_entries[0][4] == SIDECAR_NEXT
        assert h.git(host, "status", "--short").split() == ["M", ".linkml/.copier-answers.yml"]
        h.commit_all(host, f"sidecar {SIDECAR_NEXT}")

        h.update_linkmo(host, "v0.2.0")
        entries = _log(log)
        assert [entry[:5] for entry in entries[1:]] == [["linkmo", str(host), "after", "v0.1.0", "v0.2.0"]]
        changed = sorted(h.git(host, "status", "--short").split()[1::2])
        assert changed == [".copier-answers.linkmo.yml", "pets-linkmo/justfile"]


def test_the_linkmo_update_keeps_project_files_and_skips_the_copy_task(two_templates):
    host, log = two_templates
    with h.task_env(MIGRATION_LOG=str(log)):
        h.update_linkmo(host, "v0.2.0")
    project = host / "pets-linkmo"
    assert (project / "justfile").read_text(encoding="utf-8").rstrip().endswith("# added in v0.2.0")
    assert (project / "exposure.yaml").read_text(encoding="utf-8").rstrip().endswith("# the project's own line")
    datamodel = host / ".linkml" / "src" / "pets" / "datamodel"
    assert not (datamodel / "pets.py").exists() and not (datamodel / "pets_pydantic.py").exists()
    recorded = h.answers(host)
    assert recorded["_commit"] == "v0.2.0"
    assert recorded["project_slug"] == "pets" and recorded["schema_path"] == ".linkml/src/pets/schema/pets.yaml"


def test_the_root_template_waits_for_a_clean_host_but_the_sidecar_does_not(two_templates):
    host, log = two_templates
    with h.task_env(MIGRATION_LOG=str(log)):
        # linkmo's destination is the host root, so copier's dirty check covers .linkml/.
        (host / ".linkml" / "README.md").write_text("changed\n", encoding="utf-8")
        with pytest.raises(UserMessageError, match="dirty"):
            h.update_linkmo(host, "v0.2.0")
        h.git(host, "checkout", "--", ".linkml/README.md")
        # The sidecar's destination is .linkml/, and its dirty check stops there.
        (host / "pets-linkmo" / "README.md").write_text("changed\n", encoding="utf-8")
        h.update_sidecar(host, SIDECAR_NEXT)
        assert _log(log)[0][0] == "sidecar"


def test_an_update_without_the_answers_file_finds_no_template(two_templates):
    host, _ = two_templates
    with pytest.raises(UserMessageError, match="copier-answers.yml"):
        run_update(host, defaults=True, overwrite=True, unsafe=True, vcs_ref="v0.2.0", quiet=True)
