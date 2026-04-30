import mercury.columns as columns_module
import mercury.expander as expander_module
import mercury.tabs as tabs_module
from mercury.columns import Columns
from mercury.expander import Expander
from mercury.manager import WidgetsManager
from mercury.render_context import get_render_context, source_cell_context
from mercury.tabs import Tabs


def _disable_display(monkeypatch):
    monkeypatch.setattr(columns_module, "display", lambda *_: None)
    monkeypatch.setattr(expander_module, "display", lambda *_: None)
    monkeypatch.setattr(tabs_module, "display", lambda *_: None)


def setup_function():
    WidgetsManager.clear()


def teardown_function():
    WidgetsManager.clear()


def test_source_cell_context_sets_current_cell_id():
    assert get_render_context().source_cell_id is None
    assert get_render_context().render_slot_id is None
    assert get_render_context().layout_path is None

    with source_cell_context("cell-123"):
        assert get_render_context().source_cell_id == "cell-123"
        assert get_render_context().layout_stack == ()
        assert get_render_context().render_slot_id is None
        assert get_render_context().layout_path is None

    assert get_render_context().source_cell_id is None


def test_nested_layout_outputs_build_render_context_stack(monkeypatch):
    _disable_display(monkeypatch)

    with source_cell_context("cell-42"):
        tabs = Tabs(labels=["a"])
        with tabs[0]:
            tabs_ctx = get_render_context()
            tabs_slot_id = tabs_ctx.layout_stack[-1].slot_id

            cols = Columns(2)
            with cols[1]:
                cols_ctx = get_render_context()
                cols_slot_id = cols_ctx.layout_stack[-1].slot_id

                exp = Expander("Details")
                with exp:
                    exp_ctx = get_render_context()
                    exp_slot_id = exp_ctx.layout_stack[-1].slot_id

    assert tabs_ctx.source_cell_id == "cell-42"
    assert [frame.layout_type for frame in tabs_ctx.layout_stack] == ["tabs"]
    assert tabs_ctx.render_slot_id == tabs_slot_id
    assert tabs_ctx.layout_path == tabs_slot_id

    assert cols_ctx.source_cell_id == "cell-42"
    assert [frame.layout_type for frame in cols_ctx.layout_stack] == [
        "tabs",
        "columns",
    ]
    assert cols_ctx.render_slot_id == cols_slot_id
    assert cols_ctx.layout_path == f"{tabs_slot_id}/{cols_slot_id}"

    assert exp_ctx.source_cell_id == "cell-42"
    assert [frame.layout_type for frame in exp_ctx.layout_stack] == [
        "tabs",
        "columns",
        "expander",
    ]
    assert exp_ctx.render_slot_id == exp_slot_id
    assert exp_ctx.layout_path == f"{tabs_slot_id}/{cols_slot_id}/{exp_slot_id}"


def test_columns_clears_cached_outputs_by_default(monkeypatch):
    _disable_display(monkeypatch)

    outs = Columns(2)
    calls = []

    for idx, out in enumerate(outs):
        monkeypatch.setattr(
            out,
            "clear_output",
            lambda wait=True, idx=idx: calls.append((idx, wait)),
        )

    reused = Columns(2)

    assert reused is outs
    assert calls == [(0, True), (1, True)]


def test_columns_append_true_preserves_cached_outputs(monkeypatch):
    _disable_display(monkeypatch)

    outs = Columns(2)
    calls = []

    for out in outs:
        monkeypatch.setattr(
            out,
            "clear_output",
            lambda wait=True: calls.append(wait),
        )

    reused = Columns(2, append=True)

    assert reused is outs
    assert calls == []


def test_tabs_clears_cached_outputs_by_default(monkeypatch):
    _disable_display(monkeypatch)

    outs = Tabs(labels=["a", "b"])
    calls = []

    for idx, out in enumerate(outs):
        monkeypatch.setattr(
            out,
            "clear_output",
            lambda wait=True, idx=idx: calls.append((idx, wait)),
        )

    reused = Tabs(labels=["a", "b"])

    assert reused is outs
    assert calls == [(0, True), (1, True)]


def test_tabs_append_true_preserves_cached_outputs(monkeypatch):
    _disable_display(monkeypatch)

    outs = Tabs(labels=["a", "b"])
    calls = []

    for out in outs:
        monkeypatch.setattr(
            out,
            "clear_output",
            lambda wait=True: calls.append(wait),
        )

    reused = Tabs(labels=["a", "b"], append=True)

    assert reused is outs
    assert calls == []


def test_expander_clears_cached_output_by_default(monkeypatch):
    _disable_display(monkeypatch)

    out = Expander("Details")
    calls = []
    monkeypatch.setattr(out, "clear_output", lambda wait=True: calls.append(wait))

    reused = Expander("Details")

    assert reused is out
    assert calls == [True]


def test_expander_append_true_preserves_cached_output(monkeypatch):
    _disable_display(monkeypatch)

    out = Expander("Details")
    calls = []
    monkeypatch.setattr(out, "clear_output", lambda wait=True: calls.append(wait))

    reused = Expander("Details", append=True)

    assert reused is out
    assert calls == []
