import pytest

import mercury.file as file_module
from mercury.file import UploadFile, UploadedFile, UploadFileWidget
from mercury.manager import WidgetsManager


def setup_function():
    WidgetsManager.widgets.clear()


def teardown_function():
    WidgetsManager.widgets.clear()


def test_upload_file_defaults(monkeypatch):
    monkeypatch.setattr(file_module, "display", lambda *_: None)

    widget = UploadFile()

    assert widget.label == "Upload file"
    assert widget.max_file_size == "100MB"
    assert widget.multiple is False
    assert widget.position == "sidebar"
    assert widget.disabled is False
    assert widget.hidden is False


def test_upload_file_passes_constructor_arguments(monkeypatch):
    monkeypatch.setattr(file_module, "display", lambda *_: None)

    widget = UploadFile(
        label="Upload CSV",
        max_file_size="500kb",
        multiple=True,
        position="inline",
        disabled=True,
        hidden=True,
    )

    assert widget.label == "Upload CSV"
    assert widget.max_file_size == "500KB"
    assert widget.multiple is True
    assert widget.position == "inline"
    assert widget.disabled is True
    assert widget.hidden is True


@pytest.mark.parametrize("value, normalized", [
    ("1KB", "1KB"),
    ("10mb", "10MB"),
    ("2 GB", "2GB"),
])
def test_upload_file_accepts_valid_max_file_size(monkeypatch, value, normalized):
    monkeypatch.setattr(file_module, "display", lambda *_: None)

    widget = UploadFile(max_file_size=value)

    assert widget.max_file_size == normalized


@pytest.mark.parametrize("value", ["", "10", "MB", "0MB", "10TB", 10])
def test_upload_file_rejects_invalid_max_file_size(monkeypatch, value):
    monkeypatch.setattr(file_module, "display", lambda *_: None)

    with pytest.raises(ValueError, match="max_file_size"):
        UploadFile(max_file_size=value)


def test_upload_file_accessors_return_first_file_and_all_files():
    widget = UploadFileWidget()
    widget.values = [[65, 66], [67]]
    widget.filenames = ["a.txt", "b.txt"]

    assert widget.name == "a.txt"
    assert widget.value == b"AB"
    assert widget.names == ["a.txt", "b.txt"]
    assert widget.values_bytes == [b"AB", b"C"]
    assert [file.name for file in widget.files] == ["a.txt", "b.txt"]
    assert [file.value for file in widget] == [b"AB", b"C"]
    assert all(isinstance(file, UploadedFile) for file in widget.files)
