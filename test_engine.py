import pytest
from batterywise.engine import default_designs, default_profile, simulate_thermal, run_checks
from batterywise.reference_cases import get_reference_cases

def test_reference_cases_match_expected():
    for case in get_reference_cases():
        assert case["actual"] == pytest.approx(case["expected"]) if isinstance(case["expected"], (float, int)) else case["actual"] == case["expected"]

def test_temperature_state_carries_across_segments():
    d = default_designs()[0]
    result = simulate_thermal(d, default_profile(45))
    assert result[1]["start_temp_c"] == pytest.approx(result[0]["end_temp_c"])

def test_interconnect_resistance_is_included():
    d = default_designs()[0]
    assert d.total_resistance_ohm == pytest.approx(d.cell_resistance_ohm + d.interconnect_r_ohm + d.other_r_ohm)

def test_12_rules_exist_and_have_required_fields():
    checks = run_checks(default_designs()[0], default_profile())
    assert len(checks) == 12
    assert all({"id", "rule", "status", "detail", "suggestion"} <= set(c) for c in checks)

@pytest.mark.parametrize("index, expected", [
    (0, "Passed"), (1, "Passed"), (2, "Passed"), (3, "Passed"),
    (4, "Passed"), (5, "Passed"), (6, "Passed"), (7, "Passed"),
    (8, "Violated"), (9, "Passed"), (10, "Passed"), (11, "Unresolved")
])
def test_rule_status_smoke(index, expected):
    checks = run_checks(default_designs()[0], default_profile())
    assert checks[index]["status"] == expected

def test_rule_01_fails_for_incompatible_bms_series():
    d = default_designs()[0]
    d.ns = 17
    assert run_checks(d, default_profile())[0]["status"] == "Violated"

def test_rule_02_fails_for_overvoltage_charger():
    d = default_designs()[0]
    d.charger_max_v = 60
    assert run_checks(d, default_profile())[1]["status"] == "Violated"

def test_rule_03_fails_when_voltage_cutoff_is_exceeded():
    d = default_designs()[0]
    d.other_r_ohm = 0.5
    assert run_checks(d, default_profile())[2]["status"] == "Violated"

def test_rule_04_fails_when_cell_discharge_limit_is_exceeded():
    d = default_designs()[0]
    d.cell.max_discharge_a = 5
    assert run_checks(d, default_profile())[3]["status"] == "Violated"

def test_rule_05_fails_when_bms_peak_rating_is_too_low():
    d = default_designs()[0]
    d.bms_continuous_a = 20
    assert run_checks(d, default_profile())[4]["status"] == "Violated"

def test_rule_06_fails_per_cell_current():
    d = default_designs()[0]
    d.cell.max_discharge_a = 5
    assert run_checks(d, default_profile())[5]["status"] == "Violated"

def test_rule_07_fails_cell_charge_limit():
    d = default_designs()[0]
    d.cell.max_charge_a = 0.5
    assert run_checks(d, default_profile(), requested_charge_a=5)[6]["status"] == "Violated"

def test_rule_08_fails_bms_charge_limit():
    d = default_designs()[0]
    d.bms_charge_a = 2
    assert run_checks(d, default_profile(), requested_charge_a=5)[7]["status"] == "Violated"

def test_rule_09_fails_thermal_limit():
    d = default_designs()[0]
    d.cell.max_temp_c = 30
    assert run_checks(d, default_profile(45))[8]["status"] == "Violated"

def test_rule_10_fails_regen_charge_limit():
    d = default_designs()[0]
    d.cell.max_charge_a = 0.5
    assert run_checks(d, default_profile())[9]["status"] == "Violated"

def test_rule_11_fails_fuse_cable_coordination():
    d = default_designs()[0]
    d.fuse_current_a = 60
    d.cable_current_a = 40
    assert run_checks(d, default_profile())[10]["status"] == "Violated"

def test_rule_12_remains_unresolved_until_data_verified():
    assert run_checks(default_designs()[0], default_profile())[11]["status"] == "Unresolved"
