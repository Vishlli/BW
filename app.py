import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from batterywise.engine import default_designs, default_profile, simulate_thermal, run_checks
from batterywise.reference_cases import get_reference_cases

st.set_page_config(page_title="BatteryWise", layout="wide")
st.title("BatteryWise")
st.caption("Reusable battery design comparison • illustrative prototype • not for production use")

st.warning("Component and thermal values in this scaffold are illustrative. This app does not certify battery safety or regulatory compliance.")

designs = default_designs()
names = [d.name for d in designs]
selected_name = st.selectbox("Design", names)
design = next(d for d in designs if d.name == selected_name)
ambient = st.slider("Ambient temperature (°C)", min_value=15, max_value=50, value=45)
profile = default_profile(float(ambient))
thermal = simulate_thermal(design, profile)
checks = run_checks(design, profile)

tab1, tab2, tab3, tab4 = st.tabs(["Beginner", "Intermediate", "Advanced", "Expert"])
with tab1:
    st.subheader("Quick verdict")
    a,b,c = st.columns(3)
    a.metric("Nominal energy", f"{design.energy_wh:.1f} Wh")
    b.metric("Cell-only mass", f"{design.cell_mass_kg:.2f} kg")
    c.metric("Peak model temperature", f"{max(x['end_temp_c'] for x in thermal):.1f} °C")
    st.write("Start with the checks marked Violated or Unresolved. A passing software check is not a safety certification.")
with tab2:
    st.subheader("Design trade-offs")
    st.dataframe(pd.DataFrame([{
        "Design": d.name, "Voltage (V)": d.v_nom, "Capacity (Ah)": d.capacity_ah,
        "Energy (Wh)": d.energy_wh, "Cell-only mass (kg)": d.cell_mass_kg,
        "Total resistance (Ω)": d.total_resistance_ohm
    } for d in designs]), use_container_width=True)
with tab3:
    st.subheader("Model inputs")
    st.json(design.as_dict())
    st.subheader("Segment-by-segment results")
    st.dataframe(pd.DataFrame(thermal), use_container_width=True)
with tab4:
    st.subheader("Machine-readable outputs")
    st.download_button("Download run JSON", data=pd.Series({
        "design": design.as_dict(), "ambient_c": ambient, "thermal": thermal, "checks": checks
    }).to_json(), file_name="batterywise_run.json", mime="application/json")
    st.download_button("Download checks CSV", data=pd.DataFrame(checks).to_csv(index=False), file_name="batterywise_checks.csv", mime="text/csv")

st.divider()
st.subheader("Conflict explorer")
status_filter = st.multiselect("Show statuses", ["Violated", "Unresolved", "Passed"], default=["Violated", "Unresolved"])
for check in checks:
    if check["status"] not in status_filter:
        continue
    with st.expander(f'{check["id"]} · {check["status"]} · {check["rule"]}'):
        st.write(check["detail"])
        st.markdown(f'**Suggested next step:** {check["suggestion"]}')

st.subheader("Thermal profile")
fig, ax = plt.subplots()
ax.plot([x["segment"] for x in thermal], [x["end_temp_c"] for x in thermal], marker="o")
ax.set_ylabel("Estimated temperature (°C)")
ax.set_xlabel("Load segment")
ax.tick_params(axis="x", rotation=25)
st.pyplot(fig)
st.caption("Illustrative lumped model. Verify parameters and validate against measured data before using results for engineering decisions.")

st.subheader("Reference cases")
st.dataframe(pd.DataFrame(get_reference_cases()), use_container_width=True)
