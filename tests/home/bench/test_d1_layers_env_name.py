"""The D1 layer switch is ``SYMBOLIC_D1_LAYERS``; the former name ``HOMELOOP_D1_LAYERS`` is still read when the new one is unset. Pure data."""
import inspect
import pathlib

from bench.suites.home.planners import d1_options as D

NEW, OLD = "SYMBOLIC_D1_LAYERS", "HOMELOOP_D1_LAYERS"
ROOT = pathlib.Path(__file__).resolve().parents[3]


def test_new_name_is_the_switch():
    assert D.LAYERS_ENV == NEW
    assert D.selected_layers({NEW: "d3"}) == D.D3_LAYERS and D.selected_layers({NEW: "precond_repair"}) == ("precond_repair",)


def test_old_name_is_the_fallback_when_the_new_one_is_unset_or_empty(capsys):
    assert D.selected_layers({OLD: "d3"}) == D.D3_LAYERS == D.selected_layers({NEW: "", OLD: "d3"})
    assert D.selected_layers({OLD: "none"}) == ()
    assert capsys.readouterr().err == ""


def test_neither_set_is_the_default_all(capsys):
    assert D.layers_value({}) is None
    assert D.selected_layers({}) == D.ALL_LAYERS == D.selected_layers({NEW: "", OLD: ""})
    assert capsys.readouterr().err == ""


def test_both_set_and_different_the_new_one_wins_with_one_warning_line(capsys):
    D._warn_both.cache_clear()
    assert D.selected_layers({NEW: "d2", OLD: "precond_repair"}) == D.D2_LAYERS
    err = capsys.readouterr().err
    assert err.count("\n") == 1 and NEW in err and OLD in err


def test_both_set_and_equal_gives_no_warning(capsys):
    D._warn_both.cache_clear()
    assert D.selected_layers({NEW: "d3", OLD: " D3 "}) == D.D3_LAYERS
    assert capsys.readouterr().err == ""


def test_a_renamed_switch_keeps_a_made_up_list_identical():
    # regression shape: a run started with the former name must get exactly the layers the new name gives
    for v in ("all", "d3", "d2", "none", "gate_prune,precond_repair"):
        assert D.selected_layers({OLD: v}) == D.selected_layers({NEW: v})
        assert D.layer_options({OLD: v}) == D.layer_options({NEW: v})


def test_only_the_helper_names_the_old_variable_in_code():
    quoted = f'"{OLD}"'
    assert quoted in inspect.getsource(D.layers_value)
    hits = [str(p.relative_to(ROOT)) for d in ("bench", "symbolic_robot") for p in (ROOT / d).rglob("*.py") if quoted in p.read_text("utf-8")]
    assert hits == ["bench/suites/home/planners/d1_options.py"]
    assert D.__loader__.get_source(D.__name__).count(quoted) == 1
