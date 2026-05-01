import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="Classroom CO2 Tool",
    page_icon="🏫",
    layout="wide",
)

# ── Constants ─────────────────────────────────────────────────────────────────
OUTDOOR_CO2_PPM = 420
CEILING_HEIGHT_M = 2.8
OCCUPANCY_DENSITY_PER_M2 = 0.5
MIN_FLOOR_AREA_M2 = 20

boys_co2_Lps = {
    "6-<11": {
        "Seating quietly": 0.0025,
        "Seating and reading": 0.0030,
        "Standing": 0.0035,
        "Moving around in the class": 0.0040,
    },
    "11-<16": {
        "Seating quietly": 0.0034,
        "Seating and reading": 0.0041,
        "Standing": 0.0048,
        "Moving around in the class": 0.0054,
    },
}

girls_co2_Lps = {
    "6-<11": {
        "Seating quietly": 0.0023,
        "Seating and reading": 0.0027,
        "Standing": 0.0032,
        "Moving around in the class": 0.0037,
    },
    "11-<16": {
        "Seating quietly": 0.0029,
        "Seating and reading": 0.0035,
        "Standing": 0.0041,
        "Moving around in the class": 0.0047,
    },
}

ventilation_per_person_Lps = {
    "I": 10.0, "II": 7.0, "III": 4.0, "IV": 2.5,
}

ventilation_per_m2_Lps = {
    "I":   {"Very low polluting": 0.50, "Low polluting": 1.00, "Non low-polluting": 1.00},
    "II":  {"Very low polluting": 0.35, "Low polluting": 0.70, "Non low-polluting": 1.40},
    "III": {"Very low polluting": 0.20, "Low polluting": 0.40, "Non low-polluting": 0.80},
    "IV":  {"Very low polluting": 0.15, "Low polluting": 0.30, "Non low-polluting": 0.60},
}

BUILDING_TYPES  = ["Very low polluting", "Low polluting", "Non low-polluting"]
CATEGORIES      = ["I", "II", "III", "IV"]
ACTIVITY_LEVELS = [
    "Seating quietly",
    "Seating and reading",
    "Standing",
    "Moving around in the class",
]
ACTIVITY_SHORT = {
    "Seating quietly":            "Seating quietly",
    "Seating and reading":        "Seating & reading",
    "Standing":                   "Standing",
    "Moving around in the class": "Moving around",
}
AGE_GROUPS  = ["6-<11", "11-<16"]
GROUP_TYPES = ["Boys only", "Girls only", "Mixed boys + girls"]

THRESHOLDS = {
    "Acceptable": (0,    800,  "#2ecc71", "Acceptable"),
    "Good":       (800,  1000, "#f1c40f", "Good"),
    "Caution":    (1000, 1500, "#e67e22", "Caution"),
    "Poor":       (1500, 2500, "#e74c3c", "Poor"),
    "Very poor":  (2500, 99999,"#8e1a0e", "Very poor"),
}

ICONS = {
    "Acceptable": "checkmark",
    "Good":       "circle",
    "Caution":    "warning",
    "Poor":       "circle",
    "Very poor":  "warning",
}

def co2_status(ppm):
    for label, (lo, hi, colour, _) in THRESHOLDS.items():
        if lo <= ppm < hi:
            return label, colour
    return "Very poor", "#8e1a0e"

def calculate_occupants(floor_area_m2):
    return max(1, int(round(floor_area_m2 * OCCUPANCY_DENSITY_PER_M2)))

def get_generation_per_person(group_type, age_group, activity):
    if group_type == "Boys only":
        return boys_co2_Lps[age_group][activity]
    if group_type == "Girls only":
        return girls_co2_Lps[age_group][activity]
    return 0.5 * boys_co2_Lps[age_group][activity] + 0.5 * girls_co2_Lps[age_group][activity]

@st.cache_data
def build_results():
    rows = []
    for group_type in GROUP_TYPES:
        for age_group in AGE_GROUPS:
            for activity in ACTIVITY_LEVELS:
                for floor_area_m2 in range(MIN_FLOOR_AREA_M2, 105, 5):
                    occupants = calculate_occupants(floor_area_m2)
                    volume_m3 = floor_area_m2 * CEILING_HEIGHT_M
                    co2_pp    = get_generation_per_person(group_type, age_group, activity)
                    total_co2 = occupants * co2_pp
                    for category in CATEGORIES:
                        for building_type in BUILDING_TYPES:
                            pv         = occupants * ventilation_per_person_Lps[category]
                            av         = floor_area_m2 * ventilation_per_m2_Lps[category][building_type]
                            tv         = pv + av
                            ach        = tv * 3.6 / volume_m3
                            steady_co2 = OUTDOOR_CO2_PPM + (total_co2 / tv) * 1e6
                            rows.append({
                                "group_type":                    group_type,
                                "age_group":                     age_group,
                                "activity_level":                activity,
                                "floor_area_m2":                 floor_area_m2,
                                "occupants":                     occupants,
                                "volume_m3":                     volume_m3,
                                "category":                      category,
                                "building_type":                 building_type,
                                "co2_generation_per_person_Lps": co2_pp,
                                "total_co2_generation_Lps":      total_co2,
                                "people_ventilation_Lps":        pv,
                                "area_ventilation_Lps":          av,
                                "total_ventilation_Lps":         tv,
                                "ACH":                           ach,
                                "steady_state_CO2_ppm":          steady_co2,
                            })
    return pd.DataFrame(rows)

df = build_results()

# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.header("Controls")

    group_type = st.selectbox("Group type",    GROUP_TYPES,    index=2)
    age_group  = st.selectbox("Age group",     AGE_GROUPS,     index=0)
    building   = st.selectbox("Building type", BUILDING_TYPES, index=1)
    floor_area = st.slider(
        "Classroom floor area (m2)",
        min_value=MIN_FLOOR_AREA_M2, max_value=100, value=40, step=5,
    )

    st.divider()
    st.subheader("Classroom summary")
    occupants = calculate_occupants(floor_area)
    volume    = floor_area * CEILING_HEIGHT_M
    c1, c2 = st.columns(2)
    c1.metric("Floor area",  str(floor_area) + " m2")
    c2.metric("Occupants",   str(occupants))
    c1.metric("Volume",      str(round(volume, 0)) + " m3")
    c2.metric("Density",     str(OCCUPANCY_DENSITY_PER_M2) + " /m2")
    st.caption(
        "Occupancy density fixed at 0.5 persons/m2 (EN 16798). "
        "Ceiling height fixed at 2.8 m."
    )

    st.divider()
    st.subheader("CO2 status legend")
    for label, (lo, hi, colour, _) in THRESHOLDS.items():
        hi_str = str(hi) if hi < 9999 else "+"
        st.markdown(
            "<span style=\"background:" + colour + ";color:white;padding:3px 10px;"
            "border-radius:4px;font-size:0.85em\">" + label + "</span>"
            "&nbsp; " + str(lo) + " - " + hi_str + " ppm",
            unsafe_allow_html=True,
        )

    st.divider()
    csv_all = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download full dataset (CSV)",
        data=csv_all,
        file_name="classroom_co2_all_results.csv",
        mime="text/csv",
        use_container_width=True,
    )

# ═══════════════════════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════════════════════
st.title("Classroom CO2 Estimation Tool")
st.markdown(
    "Steady-state CO2 (ppm) = 420 + (generation / ventilation) x 1,000,000  "
    "using EN 16798 ventilation rates and child CO2 generation rates "
    "(Persily & de Jonge, 2017)."
)
st.divider()

# ── Filter ─────────────────────────────────────────────────────────────────────
sub = df[
    (df["group_type"]    == group_type) &
    (df["age_group"]     == age_group) &
    (df["building_type"] == building) &
    (df["floor_area_m2"] == floor_area)
].copy()

# ═══════════════════════════════════════════════════════════════════════════════
# STATUS PANEL
# ═══════════════════════════════════════════════════════════════════════════════
st.subheader("Air quality status - all categories & activities")
st.caption(
    "Building: **" + building + "**"
    " | Group: **" + group_type + "**"
    " | Age: **" + age_group + "**"
    " | Floor area: **" + str(floor_area) + " m2** (" + str(occupants) + " occupants)"
)

cat_cols = st.columns(len(CATEGORIES))

for ci, cat in enumerate(CATEGORIES):
    with cat_cols[ci]:
        st.markdown("**Category " + cat + "**")
        for act in ACTIVITY_LEVELS:
            row = sub[(sub["category"] == cat) & (sub["activity_level"] == act)]
            if row.empty:
                continue
            ppm   = float(row["steady_state_CO2_ppm"].values[0])
            ach   = float(row["ACH"].values[0])
            tv    = float(row["total_ventilation_Lps"].values[0])
            label, colour = co2_status(ppm)

            st.markdown(
                "<div style=\"background:" + colour + ";color:white;"
                "border-radius:8px;padding:10px 12px;margin-bottom:8px;"
                "font-size:0.83em;\">"
                "<b>" + ACTIVITY_SHORT[act] + "</b><br>"
                + str(round(ppm, 0))[:-2] + " ppm &nbsp;|&nbsp; "
                + str(round(tv, 1)) + " L/s &nbsp;|&nbsp; "
                + str(round(ach, 2)) + " ACH<br>"
                "<span style=\"opacity:0.92\">" + label + "</span>"
                "</div>",
                unsafe_allow_html=True,
            )

# ═══════════════════════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════════════════════
st.divider()
st.caption(
    "CO2 generation rates: Persily & de Jonge (2017), Indoor Air, doi:10.1111/ina.12383. "
    "Ventilation rates: EN 16798-1:2019, Tables B.6 and B.7. "
    "Outdoor CO2 baseline: 420 ppm."
)
