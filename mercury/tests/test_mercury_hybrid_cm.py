import asyncio

import pytest
from tornado.web import HTTPError

from mercury_app.mercury_hybrid_cm import HybridContentsManager, _norm


class FakeContentsManager:
    parent = None

    def __init__(self, files=None):
        self.files = files or {}

    def file_exists(self, path):
        return path in self.files

    def get(self, path, content=True, type=None, format=None):
        if path not in self.files:
            raise HTTPError(404, f"Missing file: {path}")
        model = dict(self.files[path])
        if not content:
            model["content"] = None
            model["format"] = None
        return model

    def save(self, model, path):
        self.files[path] = {
            "type": model.get("type"),
            "format": model.get("format"),
            "content": model.get("content"),
            "path": path,
            "name": path.rsplit("/", 1)[-1],
        }
        return dict(self.files[path])

    def dir_exists(self, path):
        prefix = path.rstrip("/") + "/"
        return any(file_path.startswith(prefix) for file_path in self.files)

    def delete(self, path):
        self.files.pop(path, None)

    def list_checkpoints(self, path):
        return []

    def create_checkpoint(self, path):
        return {"id": "checkpoint"}

    def restore_checkpoint(self, path, checkpoint_id):
        return None

    def delete_checkpoint(self, path, checkpoint_id):
        return None


def _source_notebook():
    return {
        "metadata": {
            "mercury": {"title": "App"},
            "widgets": {"application/vnd.jupyter.widget-state+json": {"state": {}}},
        },
        "cells": [
            {
                "cell_type": "code",
                "id": "cell-1",
                "source": "print('hello')",
                "execution_count": 2,
                "outputs": [{"output_type": "stream", "text": "hello"}],
            },
            {"cell_type": "markdown", "id": "cell-2", "source": "# Title"},
        ],
    }


def _manager(files=None):
    mgr = HybridContentsManager(FakeContentsManager(files))
    mgr._kernel_exists = lambda name: True
    return mgr


def test_norm_collapses_dot_prefixes_and_slashes():
    assert _norm("/./.mercury_sessions/app.ipynb") == ".mercury_sessions/app.ipynb"
    assert _norm("./folder/../folder/.mercury_sessions/app.ipynb") == (
        "folder/.mercury_sessions/app.ipynb"
    )
    assert _norm("") == ""


def test_shadow_detection_supports_root_and_nested_paths():
    assert HybridContentsManager._is_shadow(".mercury_sessions/a.ipynb")
    assert HybridContentsManager._is_shadow("./.mercury_sessions/a.ipynb")
    assert HybridContentsManager._is_shadow("folder/.mercury_sessions/a.ipynb")
    assert HybridContentsManager._is_shadow("folder/_mercury_sessions/a.ipynb")
    assert not HybridContentsManager._is_shadow("folder/app.ipynb")


def test_source_path_for_shadow_supports_root_and_nested_paths():
    assert (
        HybridContentsManager._source_path_for_shadow(
            ".mercury_sessions/report__mercury__abcd.ipynb"
        )
        == "report.ipynb"
    )
    assert (
        HybridContentsManager._source_path_for_shadow(
            "folder/.mercury_sessions/report__mercury__abcd.ipynb"
        )
        == "folder/report.ipynb"
    )
    assert (
        HybridContentsManager._source_path_for_shadow(
            "folder/sub/_mercury_sessions/app__mercury__abcd.ipynb"
        )
        == "folder/sub/app.ipynb"
    )
    assert (
        HybridContentsManager._source_path_for_shadow(
            "folder/.mercury_sessions/not-a-mercury-shadow.ipynb"
        )
        is None
    )


def test_get_recovers_missing_root_shadow_from_source_notebook():
    mgr = _manager(
        {
            "report.ipynb": {
                "type": "notebook",
                "format": "json",
                "content": _source_notebook(),
            }
        }
    )

    model = asyncio.run(mgr.get(".mercury_sessions/report__mercury__abcd.ipynb"))

    assert model["path"] == ".mercury_sessions/report__mercury__abcd.ipynb"
    assert model["type"] == "notebook"
    assert "widgets" not in model["content"]["metadata"]
    assert model["content"]["metadata"]["mercury"] == {"title": "App"}
    assert model["content"]["cells"][0]["outputs"] == []
    assert model["content"]["cells"][0]["execution_count"] is None


def test_get_recovers_missing_nested_shadow_from_source_notebook():
    mgr = _manager(
        {
            "folder/report.ipynb": {
                "type": "notebook",
                "format": "json",
                "content": _source_notebook(),
            }
        }
    )

    model = asyncio.run(
        mgr.get("folder/.mercury_sessions/report__mercury__abcd.ipynb")
    )

    assert model["path"] == "folder/.mercury_sessions/report__mercury__abcd.ipynb"
    assert "widgets" not in model["content"]["metadata"]


def test_file_exists_returns_true_for_recoverable_shadow():
    mgr = _manager(
        {
            "folder/report.ipynb": {
                "type": "notebook",
                "format": "json",
                "content": _source_notebook(),
            }
        }
    )

    exists = asyncio.run(
        mgr.file_exists("folder/.mercury_sessions/report__mercury__abcd.ipynb")
    )

    assert exists is True


def test_get_rejects_unrecoverable_missing_shadow():
    mgr = _manager({})

    with pytest.raises(HTTPError):
        asyncio.run(mgr.get(".mercury_sessions/report__mercury__abcd.ipynb"))
