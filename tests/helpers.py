"""Hosts, sidecars and renders for the template's tests.

A test host is a git repository with a .linkml/ sidecar rendered by linkml-project-copier,
the pets fixture schema in the sidecar, and the fixture records under data/. The linkmo
template is then rendered into the host root, the way a person applies it.

Three environment variables point the tests at what they need:

- LINKML_PROJECT_COPIER, a clone or URL of linkml-project-copier (the upstream URL when
  unset), and LINKML_PROJECT_COPIER_REF, the ref in it to render (main when unset).
- LINKMO_TEST_PYTHON, a Python with click, fastapi, httpx, linkml-runtime, pydantic,
  pyyaml and pytest, which runs the generated project. Tests that run it are skipped
  without it. gen-pydantic and sssom are taken from the same environment when present.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

import yaml
from copier import run_copy, run_update
from plumbum import local

TEMPLATE_ROOT = Path(__file__).resolve().parent.parent
FIXTURES = Path(__file__).resolve().parent / "fixtures"
PETS = FIXTURES / "pets"

SIDECAR_TEMPLATE = os.environ.get(
    "LINKML_PROJECT_COPIER", "https://github.com/linkml/linkml-project-copier.git"
)
SIDECAR_REF = os.environ.get("LINKML_PROJECT_COPIER_REF", "main")
PROJECT_PYTHON = os.environ.get("LINKMO_TEST_PYTHON", "")
# The folder of gen-pydantic and gen-python for the copy step: LINKMO_LINKML_BIN, else the
# environment of LINKMO_TEST_PYTHON. Copier runs tasks in plumbum's copy of the environment,
# taken when copier is imported, so it is passed through plumbum rather than os.environ.
LINKML_BIN = os.environ.get("LINKMO_LINKML_BIN") or (str(Path(PROJECT_PYTHON).parent) if PROJECT_PYTHON else "")

# The answers the linkml-sidecar skill gives linkml-project-copier, for the pets schema.
SIDECAR_ANSWERS: dict[str, Any] = {
    "project_name": "pets",
    "project_slug": "pets",
    "email": "test@example.org",
    "full_name": "Test User",
    "github_org": "example",
    "project_description": "Animals, the people who adopt them and the shelters that house them.",
    "existing_license_file": "",
    "license": "MIT",
    "copyright_year": "2026",
    "add_example": False,
    "gh_action_pypi": False,
    "gh_action_docs_preview": False,
}

# The exposure a pets project would write once the derived default is not enough: the two
# subclasses of Animal get commands of their own, and Person a better label.
PETS_EXPOSURE = """\
generator_args:
  openapi:
    expose:
      classes:
        Animal:
          path: /animal
        Dog:
          path: /dog
        Cat:
          path: /cat
        Person:
          path: /person
          label: People
        Shelter:
          path: /shelter
    overlay:
      info:
        title: Pets API
        version: 0.1.0
      paths:
        /summary:
          get:
            summary: Count the records of each exposed class
            operationId: hand.summary
            parameters:
              - in: query
                name: scope
                schema:
                  type: string
                required: false
                description: One class only, named by its command
"""


def tool(name: str) -> str | None:
    """A console script installed beside LINKMO_TEST_PYTHON, if there is one."""
    if not PROJECT_PYTHON:
        return None
    candidate = Path(PROJECT_PYTHON).parent / name
    return str(candidate) if candidate.is_file() else None


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout


def git_init(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    git(path, "init", "-q", "-b", "main")
    for key, value in (
        ("user.email", "test@example.org"),
        ("user.name", "Test"),
        ("commit.gpgsign", "false"),
        ("tag.gpgsign", "false"),
    ):
        git(path, "config", key, value)


def commit_all(path: Path, message: str) -> None:
    git(path, "add", "-A")
    git(path, "commit", "-q", "--allow-empty", "-m", message)


def mirror(source: str, ref: str, dest: Path) -> Path:
    """A bare repository with ``ref`` of ``source`` as its main branch, and the tags.

    Fetching one ref, rather than cloning, keeps a test independent of whatever other
    branches a local clone carries.
    """
    subprocess.run(["git", "init", "-q", "--bare", str(dest)], check=True)
    full_ref = ref
    if Path(source).is_dir():
        full_ref = git(Path(source), "rev-parse", "--symbolic-full-name", ref).strip() or ref
    elif not ref.startswith("refs/"):
        full_ref = f"refs/heads/{ref}"
    git(dest, "fetch", "-q", "--tags", source, f"{full_ref}:refs/heads/main")
    return dest


def snapshot_template(dest: Path, tag: str | None = None) -> Path:
    """A git repository holding the template's working tree as one commit, optionally tagged.

    copier update needs a tagged template, and the repository under test may have
    uncommitted work, so the update tests render from a snapshot.
    """
    git_init(dest)
    files = git(TEMPLATE_ROOT, "ls-files", "-co", "--exclude-standard").splitlines()
    for name in files:
        source = TEMPLATE_ROOT / name
        if source.is_file():
            target = dest / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    commit_all(dest, "template snapshot")
    if tag:
        git(dest, "tag", tag)
    return dest


def make_host(root: Path, sidecar_source: Path | None, name: str = "host") -> Path:
    """A host repository, with a pets sidecar rendered from ``sidecar_source`` when given."""
    host = root / name
    git_init(host)
    (host / "README.md").write_text("# A host project\n", encoding="utf-8")
    if sidecar_source is not None:
        run_copy(
            str(sidecar_source),
            host / ".linkml",
            data=SIDECAR_ANSWERS,
            defaults=True,
            unsafe=True,
            vcs_ref="main",
            quiet=True,
        )
        shutil.copy2(PETS / "pets.yaml", host / ".linkml" / "src" / "pets" / "schema" / "pets.yaml")
    shutil.copytree(PETS / "data", host / "data")
    commit_all(host, "a host with a pets sidecar")
    return host


def task_env(**values: str):
    """Environment variables for copier's tasks and migrations, for the length of a with block."""
    if LINKML_BIN:
        values.setdefault("LINKMO_LINKML_BIN", LINKML_BIN)
    return local.env(**values)


def render_linkmo(host: Path, data: dict[str, Any] | None = None, src: Path | None = None, vcs_ref: str = "HEAD") -> None:
    with task_env():
        run_copy(
            str(src or TEMPLATE_ROOT),
            host,
            data=data or {},
            defaults=True,
            unsafe=True,
            vcs_ref=vcs_ref,
            quiet=True,
        )


def update_linkmo(host: Path, vcs_ref: str) -> None:
    run_update(
        host,
        answers_file=".copier-answers.linkmo.yml",
        defaults=True,
        overwrite=True,
        unsafe=True,
        vcs_ref=vcs_ref,
        quiet=True,
    )


def update_sidecar(host: Path, vcs_ref: str) -> None:
    run_update(host / ".linkml", defaults=True, overwrite=True, unsafe=True, vcs_ref=vcs_ref, quiet=True)


def answers(host: Path, name: str = ".copier-answers.linkmo.yml") -> dict[str, Any]:
    return yaml.safe_load((host / name).read_text(encoding="utf-8"))


def project_env(project: Path) -> dict[str, str]:
    """The environment that runs a generated project with LINKMO_TEST_PYTHON."""
    env = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"}
    env["PYTHONPATH"] = str(project / "src")
    env["LINKMO_PYTHON"] = PROJECT_PYTHON
    sssom = tool("sssom")
    if sssom:
        env["LINKMO_SSSOM"] = sssom
    return env


def run_project(project: Path, *args: str, timeout: int = 600) -> subprocess.CompletedProcess:
    return subprocess.run(
        [PROJECT_PYTHON, *args],
        cwd=project,
        env=project_env(project),
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def run_just(project: Path, *args: str, timeout: int = 600) -> subprocess.CompletedProcess:
    """Run a recipe from the host root, the way linkml-link runs from the sidecar's justfile."""
    return subprocess.run(
        ["just", "--justfile", str(project / "justfile"), *args],
        cwd=project.parent,
        env=project_env(project),
        capture_output=True,
        text=True,
        timeout=timeout,
    )
