"""Ten deterministic smoke/reference cases; expected values are calculated from formulas."""
from .engine import default_designs, default_profile, simulate_thermal, run_checks

def get_reference_cases():
    designs = default_designs()
    baseline, lfp, improved = designs
    cases = []
    cases.append({"id":"RC01","case":"NMC nominal voltage","expected":baseline.v_nom,"unit":"V","actual":baseline.v_nom})
    cases.append({"id":"RC02","case":"NMC capacity","expected":baseline.capacity_ah,"unit":"Ah","actual":baseline.capacity_ah})
    cases.append({"id":"RC03","case":"NMC nominal energy","expected":baseline.v_nom*baseline.capacity_ah,"unit":"Wh","actual":baseline.energy_wh})
    cases.append({"id":"RC04","case":"NMC cell-only mass","expected":13*4*0.046,"unit":"kg","actual":baseline.cell_mass_kg})
    cases.append({"id":"RC05","case":"NMC cell resistance contribution","expected":13*0.020/4,"unit":"ohm","actual":baseline.cell_resistance_ohm})
    cases.append({"id":"RC06","case":"Total resistance includes interconnect and other","expected":0.065+0.010+0.005,"unit":"ohm","actual":baseline.total_resistance_ohm})
    cases.append({"id":"RC07","case":"LFP nominal voltage","expected":15*3.2,"unit":"V","actual":lfp.v_nom})
    cases.append({"id":"RC08","case":"LFP nominal energy","expected":15*3.2*2*6.0,"unit":"Wh","actual":lfp.energy_wh})
    profile = default_profile(45)
    thermal = simulate_thermal(baseline, profile)
    cases.append({"id":"RC09","case":"Thermal state carried across profile","expected":True,"unit":"bool","actual":len(thermal)==len(profile) and abs(thermal[1]["start_temp_c"]-thermal[0]["end_temp_c"])<1e-9})
    checks = run_checks(baseline, profile)
    cases.append({"id":"RC10","case":"Exactly 12 checks emitted","expected":12,"unit":"count","actual":len(checks)})
    return cases
