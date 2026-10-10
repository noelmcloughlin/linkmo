"""Fixtures for the template's tests: linkml-project-copier at a ref, and rendered hosts."""

from __future__ import annotations

import warnings
from pathlib import Path

import pytest

from tests import helpers as h


@pytest.fixture(scope="session")
def sidecar_template(tmp_path_factory) -> Path:
    """linkml-project-copier at the ref under test, as a bare mirror."""
    return h.mirror(h.SIDECAR_TEMPLATE, h.SIDECAR_REF, tmp_path_factory.mktemp("lpc") / "lpc.git")


@pytest.fixture(scope="session")
def pets_host(tmp_path_factory, sidecar_template) -> tuple[Path, list[warnings.WarningMessage]]:
    """A host with a pets sidecar, and the linkmo project rendered with every default."""
    host = h.make_host(tmp_path_factory.mktemp("pets"), sidecar_template)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        h.render_linkmo(host)
    return host, list(caught)


needs_project_python = pytest.mark.skipif(
    not h.PROJECT_PYTHON, reason="set LINKMO_TEST_PYTHON to run the generated project"
)
