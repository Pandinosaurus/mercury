import pytest
from traitlets import TraitError

import mercury.date as date_module
import mercury.datetime_input as datetime_module
import mercury.daterange as daterange_module
import mercury.time as time_module
from mercury.date import DateInput, DateInputWidget
from mercury.datetime_input import DateTimeInput, DateTimeInputWidget
from mercury.daterange import DateRange, DateRangeWidget
from mercury.manager import WidgetsManager
from mercury.render_context import source_cell_context
from mercury.time import TimeInput, TimeInputWidget
from mercury.url_params import clear_runtime_url_params, set_runtime_url_params


def _disable_display(monkeypatch):
    monkeypatch.setattr(date_module, "display", lambda *_: None)
    monkeypatch.setattr(time_module, "display", lambda *_: None)
    monkeypatch.setattr(datetime_module, "display", lambda *_: None)
    monkeypatch.setattr(daterange_module, "display", lambda *_: None)


def setup_function():
    WidgetsManager.clear()
    clear_runtime_url_params()


def teardown_function():
    WidgetsManager.clear()
    clear_runtime_url_params()


@pytest.mark.parametrize(
    ("widget_cls", "label"),
    [
        (DateInputWidget, "Date"),
        (TimeInputWidget, "Time"),
        (DateTimeInputWidget, "Date and time"),
        (DateRangeWidget, "Date range"),
    ],
)
def test_temporal_widget_trait_defaults(widget_cls, label):
    widget = widget_cls()
    assert widget.label == label
    assert widget.disabled is False
    assert widget.hidden is False
    assert widget.position == "sidebar"
    assert widget.source_cell_id is None
    assert widget.render_slot_id is None
    assert widget.layout_path is None


@pytest.mark.parametrize(
    "widget_cls",
    [DateInputWidget, TimeInputWidget, DateTimeInputWidget, DateRangeWidget],
)
def test_temporal_widget_invalid_position_raises_traiterror(widget_cls):
    widget = widget_cls()
    with pytest.raises(TraitError):
        widget.position = "top"


def test_dateinput_normalizes_invalid_value(monkeypatch):
    _disable_display(monkeypatch)
    with pytest.warns(UserWarning, match="not a valid"):
        widget = DateInput(value="2026-02-30")
    assert widget.value == ""


def test_timeinput_normalizes_invalid_step(monkeypatch):
    _disable_display(monkeypatch)
    with pytest.warns(UserWarning, match="step.*not an integer"):
        widget = TimeInput(value="14:30", step="abc")
    assert widget.step == 60


def test_datetimeinput_clamps_to_max(monkeypatch):
    _disable_display(monkeypatch)
    with pytest.warns(UserWarning, match="after `max`"):
        widget = DateTimeInput(
            value="2026-05-01 12:00",
            max="2026-04-30 23:59",
        )
    assert widget.value == "2026-04-30 23:59"


def test_daterange_swaps_reversed_range(monkeypatch):
    _disable_display(monkeypatch)
    with pytest.warns(UserWarning, match="start value is after end value"):
        widget = DateRange(value=("2026-04-30", "2026-04-01"))
    assert widget.value == ["2026-04-01", "2026-04-30"]


def test_dateinput_uses_url_param_when_valid(monkeypatch):
    _disable_display(monkeypatch)
    set_runtime_url_params({"day": ["2026-04-30"]})
    widget = DateInput(value="2026-04-01", url_key="day")
    assert widget.value == "2026-04-30"


def test_timeinput_uses_url_param_when_valid(monkeypatch):
    _disable_display(monkeypatch)
    set_runtime_url_params({"at": ["14:30"]})
    widget = TimeInput(value="09:00", url_key="at")
    assert widget.value == "14:30"


def test_datetimeinput_uses_url_param_when_valid(monkeypatch):
    _disable_display(monkeypatch)
    set_runtime_url_params({"at": ["2026-04-30 14:30"]})
    widget = DateTimeInput(value="2026-04-01 09:00", url_key="at")
    assert widget.value == "2026-04-30 14:30"


def test_datetimeinput_accepts_browser_datetime_separator(monkeypatch):
    _disable_display(monkeypatch)
    widget = DateTimeInput(value="2026-04-30T14:30")
    assert widget.value == "2026-04-30 14:30"


def test_daterange_uses_url_params_when_valid(monkeypatch):
    _disable_display(monkeypatch)
    set_runtime_url_params({"start": ["2026-04-01"], "end": ["2026-04-30"]})
    widget = DateRange(
        value=("2026-01-01", "2026-01-31"),
        start_url_key="start",
        end_url_key="end",
    )
    assert widget.value == ["2026-04-01", "2026-04-30"]


@pytest.mark.parametrize(
    ("module", "widget_cls"),
    [
        (date_module, DateInputWidget),
        (time_module, TimeInputWidget),
        (datetime_module, DateTimeInputWidget),
        (daterange_module, DateRangeWidget),
    ],
)
def test_temporal_repr_mimebundle_adds_mercury_metadata(monkeypatch, module, widget_cls):
    base_result = [
        {"text/plain": "foo", "application/vnd.jupyter.widget-view+json": {}},
        {"something_else": "bar"},
    ]

    def fake_super_repr(self, **kwargs):
        return [dict(base_result[0]), dict(base_result[1])]

    monkeypatch.setattr(module.anywidget.AnyWidget, "_repr_mimebundle_", fake_super_repr)

    widget = widget_cls(position="inline")
    data = widget._repr_mimebundle_()

    assert len(data) == 2
    assert module.MERCURY_MIMETYPE in data[0]
    metadata = data[0][module.MERCURY_MIMETYPE]
    assert metadata["widget"] == type(widget).__qualname__
    assert metadata["position"] == "inline"
    assert isinstance(metadata["model_id"], str)
    assert metadata["model_id"]
    assert "text/plain" not in data[0]


@pytest.mark.parametrize(
    ("factory", "kwargs"),
    [
        (DateInput, {"value": "2026-04-30"}),
        (TimeInput, {"value": "14:30"}),
        (DateTimeInput, {"value": "2026-04-30 14:30"}),
        (DateRange, {"value": ("2026-04-01", "2026-04-30")}),
    ],
)
def test_temporal_widgets_get_source_cell_metadata(monkeypatch, factory, kwargs):
    _disable_display(monkeypatch)
    with source_cell_context("cell-temporal"):
        widget = factory(**kwargs)

    assert widget.source_cell_id == "cell-temporal"
    assert widget.cell_id == "cell-temporal"
    assert widget.render_slot_id is None
    assert widget.layout_path is None
