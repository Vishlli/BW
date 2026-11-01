"""BatteryWise illustrative calculation engine. Not for production battery design."""
from dataclasses import dataclass, asdict
from typing import List, Dict, Any
import math

@dataclass
class Cell:
    name: str
    chemistry: str
    v_nom: float
    capacity_ah: float
    r_ohm: float
    mass_kg: float
    max_discharge_a: float
    max_charge_a: float
    min_v: float
    max_v: float
    max_temp_c: float

@dataclass
class Design:
    name: str
    cell: Cell
    ns: int
    np: int
    interconnect_r_ohm: float
    other_r_ohm: float
    thermal_resistance_k_w: float
    thermal_capacitance_j_k: float
    bms_series_min: int
    bms_series_max: int
    bms_continuous_a: float
    bms_charge_a: float
    charger_max_v: float
    fuse_current_a: float
    cable_current_a: float
    mass_limit_kg: float = 18.0
    enclosure_volume_limit_l: float = 20.0

    @property
    def v_nom(self): return self.ns * self.cell.v_nom
    @property
    def capacity_ah(self): return self.np * self.cell.capacity_ah
    @property
    def energy_wh(self): return self.v_nom * self.capacity_ah
    @property
    def cell_mass_kg(self): return self.ns * self.np * self.cell.mass_kg
    @property
    def cell_resistance_ohm(self): return self.ns * self.cell.r_ohm / self.np
    @property
    def total_resistance_ohm(self):
        return self.cell_resistance_ohm + self.interconnect_r_ohm + self.other_r_ohm
    @property
    def max_pack_v(self): return self.ns * self.cell.max_v
    @property
    def min_pack_v(self): return self.ns * self.cell.min_v
    def as_dict(self):
        d = asdict(self)
        d["cell"] = asdict(self.cell)
        d.update({"nominal_voltage_v": self.v_nom, "capacity_ah": self.capacity_ah,
                  "nominal_energy_wh": self.energy_wh, "cell_mass_kg": self.cell_mass_kg,
                  "cell_resistance_ohm": self.cell_resistance_ohm,
                  "total_resistance_ohm": self.total_resistance_ohm})
        return d

@dataclass
class Segment:
    name: str
    current_a: float
    duration_s: int
    ambient_c: float

def simulate_thermal(design: Design, profile: List[Segment], initial_temp_c=None) -> List[Dict[str, Any]]:
    """Lumped thermal model; temperature is carried from one segment to the next."""
    temp = profile[0].ambient_c if initial_temp_c is None else initial_temp_c
    out = []
    rth = max(design.thermal_resistance_k_w, 1e-9)
    cth = max(design.thermal_capacitance_j_k, 1e-9)
    for s in profile:
        # Ambient may change between segments; retain cell's temperature state.
        p_heat = (s.current_a ** 2) * design.total_resistance_ohm
        # First-order lumped response over this segment.
        tau = rth * cth
        target = s.ambient_c + p_heat * rth
        temp_end = target + (temp - target) * math.exp(-s.duration_s / tau)
        out.append({
            "segment": s.name, "current_a": s.current_a, "duration_s": s.duration_s,
            "ambient_c": s.ambient_c, "start_temp_c": temp, "end_temp_c": temp_end,
            "heat_w": p_heat, "voltage_sag_v": abs(s.current_a) * design.total_resistance_ohm,
            "terminal_voltage_est_v": design.v_nom - s.current_a * design.total_resistance_ohm
        })
        temp = temp_end
    return out

def run_checks(design: Design, profile: List[Segment], requested_charge_a=5.0,
               requested_peak_a=35.0, expected_fuse_a=40.0) -> List[Dict[str, str]]:
    thermal = simulate_thermal(design, profile)
    peak_temp = max(x["end_temp_c"] for x in thermal)
    max_discharge = max([s.current_a for s in profile] + [0])
    max_charge = max([abs(s.current_a) for s in profile if s.current_a < 0] + [0])
    max_cell_current = max_discharge / design.np
    min_terminal = min(x["terminal_voltage_est_v"] for x in thermal)
    # The checks deliberately distinguish violation from missing/assumed data.
    checks = [
        ("R01", "BMS series compatibility", "Passed" if design.bms_series_min <= design.ns <= design.bms_series_max else "Violated",
         f"Pack is {design.ns}S; BMS range is {design.bms_series_min}S–{design.bms_series_max}S.",
         "Select a BMS whose supported series count includes this pack."),
        ("R02", "Charger maximum voltage", "Passed" if design.charger_max_v <= design.max_pack_v + 1e-9 else "Violated",
         f"Charger max {design.charger_max_v:.2f} V; pack max {design.max_pack_v:.2f} V.",
         "Choose a chemistry- and series-compatible charger."),
        ("R03", "Minimum voltage / cutoff", "Passed" if min_terminal >= design.min_pack_v else "Violated",
         f"Estimated minimum terminal voltage {min_terminal:.2f} V; pack minimum {design.min_pack_v:.2f} V.",
         "Reduce load, increase parallel count, or use a validated voltage model."),
        ("R04", "Continuous cell discharge", "Passed" if max_discharge / design.np <= design.cell.max_discharge_a else "Violated",
         f"Peak profile current per parallel path {max_cell_current:.2f} A; cell limit {design.cell.max_discharge_a:.2f} A.",
         "Increase parallel count or choose a cell with a suitable verified rating."),
        ("R05", "Peak BMS discharge", "Passed" if requested_peak_a <= design.bms_continuous_a else "Violated",
         f"Requested peak {requested_peak_a:.1f} A; configured BMS rating {design.bms_continuous_a:.1f} A.",
         "Select a BMS rated for the required current and duration."),
        ("R06", "Per-cell current", "Passed" if max_cell_current <= design.cell.max_discharge_a else "Violated",
         f"Approximate per-cell current {max_cell_current:.2f} A.",
         "Increase parallel count or reduce the requested current."),
        ("R07", "Cell charge-current limit", "Passed" if requested_charge_a / design.np <= design.cell.max_charge_a else "Violated",
         f"Charge current per parallel path {requested_charge_a/design.np:.2f} A; cell limit {design.cell.max_charge_a:.2f} A.",
         "Reduce charge current or select a cell with a verified higher charge rating."),
        ("R08", "BMS charge-current limit", "Passed" if requested_charge_a <= design.bms_charge_a else "Violated",
         f"Requested charge {requested_charge_a:.1f} A; BMS charge rating {design.bms_charge_a:.1f} A.",
         "Use a compatible BMS with sufficient charge-current rating."),
        ("R09", "Thermal limit", "Passed" if peak_temp <= design.cell.max_temp_c else "Violated",
         f"Predicted peak {peak_temp:.1f}°C; configured cell limit {design.cell.max_temp_c:.1f}°C.",
         "Verify the model, reduce load, improve thermal path, or apply validated derating."),
        ("R10", "Regenerative charging", "Passed" if max_charge / design.np <= design.cell.max_charge_a else "Violated",
         f"Peak profile charging current per parallel path {max_charge/design.np:.2f} A.",
         "Limit regen current to the verified cell and BMS charge limits."),
        ("R11", "Fuse/cable coordination", "Passed" if design.fuse_current_a <= design.cable_current_a and design.fuse_current_a >= expected_fuse_a else "Violated",
         f"Fuse {design.fuse_current_a:.1f} A; cable rating {design.cable_current_a:.1f} A; provisional expected fuse {expected_fuse_a:.1f} A.",
         "Coordinate fuse, cable, interrupt rating, fault current, and time-current curve."),
        ("R12", "Critical data completeness", "Unresolved",
         "This starter uses illustrative component and thermal values; exact manufacturer verification is not yet attached.",
         "Attach exact datasheets and mark each critical field verified before relying on this result.")
    ]
    return [{"id": a, "rule": b, "status": c, "detail": d, "suggestion": e}
            for a,b,c,d,e in checks]

def default_components():
    nmc = Cell("P28A demo record", "NMC", 3.6, 2.8, 0.020, 0.046,
               10.0, 2.8, 2.5, 4.2, 60.0)
    lfp = Cell("32700 6Ah demo record", "LFP", 3.2, 6.0, 0.008, 0.140,
               18.0, 3.0, 2.5, 3.65, 55.0)
    return nmc, lfp

def default_designs():
    nmc, lfp = default_components()
    return [
        Design("Baseline NMC 13S4P", nmc, 13, 4, 0.010, 0.005, 1.2, 500.0,
               10, 16, 40, 10, 54.6, 40, 50),
        Design("LFP alternative 15S2P", lfp, 15, 2, 0.010, 0.005, 0.9, 650.0,
               15, 16, 40, 10, 54.75, 40, 50),
        Design("NMC improved thermal path", nmc, 13, 4, 0.010, 0.005, 0.7, 500.0,
               10, 16, 40, 10, 54.6, 40, 50),
    ]

def default_profile(ambient_c=45.0):
    return [
        Segment("Idle/accessories", 2.0, 300, ambient_c),
        Segment("Cruise", 10.0, 1200, ambient_c),
        Segment("Sustained hill climb", 25.0, 300, ambient_c),
        Segment("Peak acceleration", 35.0, 10, ambient_c),
        Segment("Regenerative charging", -5.0, 10, ambient_c),
        Segment("Rest", 0.0, 300, ambient_c),
    ]
