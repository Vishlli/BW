# BatteryWise starter prototype

A runnable Streamlit scaffold for a battery-pack design comparison. The values are **illustrative inputs for software demonstration**, not a production design or verified bill of materials.

## Run
```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

## Tests
```bash
pytest -q
```

## Included
- Three example designs: NMC baseline, LFP alternative, NMC with improved thermal path.
- Series/parallel pack arithmetic, cell + interconnect resistance, voltage-sag estimate.
- Segment-by-segment lumped thermal model that carries temperature between load segments.
- 12 rule checks, each with a status, explanation, and suggested corrective action.
- Ten reference cases and pytest coverage for positive/negative rule outcomes.
- Streamlit conflict explorer and temperature-profile plot.

## Important
- Cell/BMS/charger/fuse/cable parameters are demo values until verified against exact manufacturer datasheets.
- The LFP example is not a verified, energy-matched design. Replace its cell data and series/parallel count after datasheet verification.
- Thermal resistance and thermal capacitance are illustrative. Do not use the predicted temperatures to design or operate a real battery pack.
- This prototype does not certify safety or regulatory compliance.
