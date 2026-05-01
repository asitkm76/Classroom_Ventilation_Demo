import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Classroom CO2 Tool",
    page_icon="🏫",
    layout="wide",
)

sns.set_theme(style="whitegrid", context="talk")

# ── Constants ─────────────────────────────────────────────────────────────────
OUTDOOR_CO2_PPM = 420
CEILING_HEIGHT_M = 2.8
OCCUPANCY_DENSITY_PER_M2 = 0.5
MIN_FLOOR_AREA_M2 = 20

boys_co2_Lps = {
    "6–<11": {
        "Seating quietly": 0.0025,
        "Seating and reading": 0.0030,
        "Standing": 0.0035,
        "Moving around in the class": 0.0040,
    },
    "11–<16": {
        "Seating quietly": 0.0034,
        "Seating and reading": 0.0041,
        "Standing": 0.0048,
        "Moving around in the class": 0.0054,
    },
}

girls_co2_Lps = {
    "6–<11": {
        "Seating quietly": 0.0023,
        "Seating and reading": 0.0027,
        "Standing": 0.0032,
        "Moving around in the class": 0.0037,
    },
    "11–<16": {
        "Seating quietly": 0.0029,
        "Seating and reading": 0.0035,
        "Standing": 0.0041,
        "Moving around in the class": 0.0047,
    },
}

# EN 16798 — people-based ventilation (Table B.6), Categories I–IV only
ventilation_per_person_Lps = {
    "I": 10.0, "II": 7.0, "III": 4.0, "IV": 2.5,
}

# EN 16798 — area-based ventilation (Table B.7),
# building types: Very low / Low / Non low-polluting only
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
    "Seating quietly":             "Seating quietly",
    "Seating and reading":         "Seating & reading",
    "Standing":                    "Standing",
    "Moving around in the class":  "Moving around",
}
AGE_GROUPS  = ["6–<11", "11–<16"]
GROUP_TYPES = ["Boys only", "Girls only", "Mixed boys + girls"]

METRIC_MAP = {
    "Steady-state CO2 (ppm)":     ("steady_state_CO2_ppm",      "Steady-state CO2 (ppm)"),
    "Total ventilation (L/s)":    ("total_ventilation_Lps",     "Total ventilation (L/s)"),
    "Air changes per hour (ACH)": ("ACH",                       "Air changes per hour"),
    "CO2 generation (L/s)":       ("total_co2_generation_Lps", "Total CO2 generation (L/s)"),
    "People ventilation (L/s)":   ("people_ventilation_Lps",    "People-based ventilation (L/s)"),
    "Area ventilation (L/s)":     ("area_ventilation_Lps",      "Area-based ventilation (L/s)"),
}
PALETTE_MAP = {
    "Steady-state CO2 (ppm)":     "YlOrRd",
    "Total ventilation (L/s)":    "viridis",
    "Air changes per hour (ACH)": "crest",
    "CO2 generation (L/s)":       "magma",
    "People ventilation (L/s)":   "Blues",
    "Area ventilation (L/s)":     "flare",
}

# ── CO2 thresholds ─────────────────────────────────────────────────────────────
THRESHOLDS = {
    "Acceptable": (0,    800,  "#2ecc71", "✅"),
    "Good":       (800,  1000, "#f1c40f", "🟡"),
    "Caution":    (1000, 1500, "#e67e22", "⚠️"),
    "Poor":       (1500, 2500, "#e74c3c", "🔴"),
    "Very poor":  (2500, 99999,"#8e1a0e", "🚨"),
}

def co2_status(ppm):
    for label, (lo, hi, colour, icon) in THRESHOLDS.items():
        if lo <= ppm < hi:
            return label, colour, icon
    return "Very poor", "#8e1a0e", "🚨"

# ── Helpers ────────────────────────────────────────────────────────────────────
def calculate_occupants(floor_area_m2):
    return max(1, int(round(floor_area_m2 * OCCUPANCY_DENSITY_PER_M2)))

def get_generation_per_person(group_type, age_group, activity):
    if group_type == "Boys only":
        return boys_co2_Lps[age_group][activity]
    if group_type == "Girls only":
        return girls_co2_Lps[age_group][activity]
    return 0.5 * boys_co2_Lps[age_group][activity] + 0.5 * girls_co2_Lps[age_group][activity]

# ── Build results table (cached) ──────────────────────────────────────────────
@st.cache_data
def build_results():
    rows = []
    for group_type in GROUP_TYPES:
        for age_group in AGE_GROUPS:
            for activity in ACTIVITY_LEVELS:
                for floor_area_m2 in range(MIN_FLOOR_AREA_M2, 105, 5):
                    occupants    = calculate_occupants(floor_area_m2)
                    volume_m3    = floor_area_m2 * CEILING_HEIGHT_M
                    co2_pp       = get_generation_per_person(group_type, age_group, activity)
                    total_co2    = occupants * co2_pp
                    for category in CATEGORIES:
                        for building_type in BUILDING_TYPES:
                            pv         = occupants * ventilation_per_person_Lps[category]
                            av         = floor_area_m2 * ventilation_per_m2_Lps[category][building_type]
                            tv         = pv + av
                            ach        = tv * 3.6 / volume_m3
                            steady_co2 = OUTDOOR_CO2_PPM + (total_co2 / tv) * 1e6
                            rows.append({
                                "group_type":                   group_type,
                                "age_group":                    age_group,
                                "activity_level":               activity,
                                "floor_area_m2":                floor_area_m2,
                                "occupants":                    occupants,
                                "volume_m3":                    volume_m3,
                                "category":                     category,
                                "building_type":                building_type,
                                "co2_generation_per_person_Lps": co2_pp,
                                "total_co2_generation_Lps":     total_co2,
                                "people_ventilation_Lps":       pv,
                                "area_ventilation_Lps":         av,
                                "total_ventilation_Lps":        tv,
                                "ACH":                          ach,
                                "steady_state_CO2_ppm":         steady_co2,
                            })
    return pd.DataFrame(rows)

df = build_results()

# ═════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.header("⚙️ Controls")

    group_type   = st.selectbox("Group type",    GROUP_TYPES,   index=2)
    age_group    = st.selectbox("Age group",     AGE_GROUPS,    index=0)
    building     = st.selectbox("Building type", BUILDING_TYPES, index=1)
    floor_area   = st.slider(
        "Classroom floor area (m²)",
        min_value=MIN_FLOOR_AREA_M2, max_value=100, value=40, step=5,
    )
    metric_label = st.selectbox("Metric to visualise", list(METRIC_MAP.keys()))
    chart_type   = st.radio("Chart type", ["Bar chart", "Heatmap"])

    st.divider()
    st.subheader("📐 Classroom summary")
    occupants = calculate_occupants(floor_area)
    volume    = floor_area * CEILING_HEIGHT_M
    c1, c2 = st.columns(2)
    c1.metric("Floor area",  f"{floor_area} m²")
    c2.metric("Occupants",   f"{occupants}")
    c1.metric("Volume",      f"{volume:.0f} m³")
    c2.metric("Density",     f"{OCCUPANCY_DENSITY_PER_M2} /m²")
    st.caption(
        "Occupancy density fixed at 0.5 persons/m² (EN 16798). "
        "Ceiling height fixed at 2.8 m."
    )

    st.divider()
    st.subheader("🎨 CO₂ status legend")
    for label, (lo, hi, colour, icon) in THRESHOLDS.items():
        hi_str = str(hi) if hi < 9999 else "+"
        st.markdown(
            f'<span style="background:{colour};color:white;padding:2px 8px;'
            f'border-radius:4px;font-size:0.85em">{icon} {label}</span>'
            f'&nbsp; {lo}–{hi_str} ppm',
            unsafe_allow_html=True,
        )

# ═════════════════════════════════════════════════════════════════════════════
# HEADER
# ═════════════════════════════════════════════════════════════════════════════
st.title("🏫 Classroom CO₂ Estimation Tool")
st.markdown(
    "Estimate steady-state CO₂ concentrations for different classroom configurations "
    "using EN 16798 ventilation design values and child CO₂ generation rates "
    "(Persily & de Jonge, 2017).  
"
    "**CO₂ (ppm) = 420 + (generation / ventilation) × 10⁶**"
)
st.divider()

# ── Filter data ────────────────────────────────────────────────────────────────
metric_col, y_label = METRIC_MAP[metric_label]
palette = PALETTE_MAP[metric_label]

sub = df[
    (df["group_type"]    == group_type) &
    (df["age_group"]     == age_group) &
    (df["building_type"] == building) &
    (df["floor_area_m2"] == floor_area)
].copy()
sub["activity_short"] = sub["activity_level"].map(ACTIVITY_SHORT)

# ═════════════════════════════════════════════════════════════════════════════
# STATUS PANEL  — category columns × activity rows
# ═════════════════════════════════════════════════════════════════════════════
st.subheader("🚦 Air quality status — all categories & activities")
st.caption(
    f"Building: **{building}** | Group: **{group_type}** | "
    f"Age: **{age_group}** | Floor area: **{floor_area} m²** ({occupants} occupants)"
)

status_cols = st.columns(len(CATEGORIES))
for ci, cat in enumerate(CATEGORIES):
    with status_cols[ci]:
        st.markdown(f"**Category {cat}**")
        for act in ACTIVITY_LEVELS:
            row = sub[(sub["category"] == cat) & (sub["activity_level"] == act)]
            if row.empty:
                continue
            ppm = float(row["steady_state_CO2_ppm"].values[0])
            label, colour, icon = co2_status(ppm)
            st.markdown(
                f'<div style="background:{colour};color:white;border-radius:6px;'
                f'padding:7px 9px;margin-bottom:6px;font-size:0.82em;">'
                f'<b>{ACTIVITY_SHORT[act]}</b><br>'
                f'{icon} {ppm:.0f} ppm<br>'
                f'<span style="opacity:0.9">{label}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

st.divider()

# ═════════════════════════════════════════════════════════════════════════════
# CHART
# ═════════════════════════════════════════════════════════════════════════════
st.subheader(f"📊 {metric_label}")
chart_title = (
    f"{metric_label}  |  {group_type}, age {age_group}  |  "
    f"{building}  |  {floor_area} m², {occupants} occupants"
)

fig, ax = plt.subplots(figsize=(11, 5.5))
activity_order = [ACTIVITY_SHORT[a] for a in ACTIVITY_LEVELS]

if chart_type == "Heatmap":
    pivot = sub.pivot(index="category", columns="activity_level", values=metric_col)
    pivot = pivot[[a for a in ACTIVITY_LEVELS if a in pivot.columns]]
    pivot.columns = [ACTIVITY_SHORT[c] for c in pivot.columns]

    if metric_col == "steady_state_CO2_ppm":
        # draw threshold-coloured cells manually
        nrows, ncols2 = len(pivot.index), len(pivot.columns)
        for ri, row_idx in enumerate(pivot.index):
            for ci2, col_idx in enumerate(pivot.columns):
                val = pivot.loc[row_idx, col_idx]
                _, colour, _ = co2_status(val)
                ax.add_patch(mpatches.FancyBboxPatch(
                    (ci2, nrows - 1 - ri), 1, 1,
                    boxstyle="square,pad=0", linewidth=0.5,
                    edgecolor="white", facecolor=colour,
                    transform=ax.transData, zorder=0,
                ))
                ax.text(ci2 + 0.5, nrows - 0.5 - ri,
                        f"{val:.0f}", ha="center", va="center",
                        fontsize=12, color="white", fontweight="bold", zorder=1)
        ax.set_xlim(0, ncols2)
        ax.set_ylim(0, nrows)
        ax.set_xticks([i + 0.5 for i in range(ncols2)])
        ax.set_xticklabels(pivot.columns, fontsize=10)
        ax.set_yticks([i + 0.5 for i in range(nrows)])
        ax.set_yticklabels(list(reversed(pivot.index)), fontsize=10)
        ax.set_xlabel("Activity level", fontsize=11)
        ax.set_ylabel("EN 16798 category", fontsize=11)
        legend_patches = [
            mpatches.Patch(
                color=col,
                label=f"{lbl}  ({lo}–{hi if hi < 9999 else '+'} ppm)"
            )
            for lbl, (lo, hi, col, _) in THRESHOLDS.items()
        ]
        ax.legend(handles=legend_patches, bbox_to_anchor=(1.02, 1),
                  loc="upper left", fontsize=9, title="CO₂ status")
    else:
        sns.heatmap(
            pivot, annot=True, fmt=".2f", cmap=palette,
            linewidths=0.5, cbar_kws={"label": y_label, "shrink": 0.8},
            annot_kws={"size": 11}, ax=ax,
        )
        ax.set_xlabel("Activity level")
        ax.set_ylabel("EN 16798 category")

else:  # Bar chart
    sns.barplot(
        data=sub, x="activity_short", y=metric_col,
        hue="category", palette="tab10",
        order=activity_order, errorbar=None, ax=ax,
    )
    if metric_col == "steady_state_CO2_ppm":
        ymax = sub[metric_col].max() * 1.15
        for lbl, (lo, hi, colour, _) in THRESHOLDS.items():
            if lo < ymax:
                ax.axhspan(lo, min(hi, ymax), alpha=0.07, color=colour, zorder=0)
        for lbl, (lo, hi, colour, _) in THRESHOLDS.items():
            if 0 < lo < ymax:
                ax.axhline(lo, color=colour, linewidth=0.9,
                           linestyle="--", zorder=1, alpha=0.7)
    ax.set_xlabel("Activity level")
    ax.set_ylabel(y_label)
    ax.legend(title="Category", bbox_to_anchor=(1.02, 1), loc="upper left")

ax.set_title(chart_title, fontsize=12)
plt.tight_layout()
st.pyplot(fig, use_container_width=True)
plt.close()

# ═════════════════════════════════════════════════════════════════════════════
# FULL STATUS SUMMARY TABLE
# ═════════════════════════════════════════════════════════════════════════════
st.divider()
st.subheader("📋 Full results table")

summary = sub[[
    "category", "activity_level",
    "steady_state_CO2_ppm", "total_ventilation_Lps", "ACH",
    "people_ventilation_Lps", "area_ventilation_Lps",
]].copy()

summary["Status"] = summary["steady_state_CO2_ppm"].apply(
    lambda v: co2_status(v)[2] + " " + co2_status(v)[0]
)
summary = summary.rename(columns={
    "category":               "Category",
    "activity_level":         "Activity",
    "steady_state_CO2_ppm":   "CO2 (ppm)",
    "total_ventilation_Lps":  "Total vent. (L/s)",
    "people_ventilation_Lps": "People vent. (L/s)",
    "area_ventilation_Lps":   "Area vent. (L/s)",
    "ACH":                    "ACH",
})

def colour_status_cell(val):
    mapping = {
        "Acceptable": "#2ecc71", "Good": "#f1c40f",
        "Caution":    "#e67e22", "Poor": "#e74c3c", "Very poor": "#8e1a0e",
    }
    for k, c in mapping.items():
        if k in val:
            return f"background-color:{c};color:white;font-weight:bold"
    return ""

styled = (
    summary[["Category", "Activity", "CO2 (ppm)",
             "Total vent. (L/s)", "People vent. (L/s)",
             "Area vent. (L/s)", "ACH", "Status"]]
    .sort_values(["Category", "Activity"])
    .reset_index(drop=True)
    .style
    .applymap(colour_status_cell, subset=["Status"])
    .format({
        "CO2 (ppm)":           "{:.0f}",
        "Total vent. (L/s)":   "{:.2f}",
        "People vent. (L/s)":  "{:.2f}",
        "Area vent. (L/s)":    "{:.2f}",
        "ACH":                 "{:.2f}",
    })
)
st.dataframe(styled, use_container_width=True, hide_index=True)

# ── Download ───────────────────────────────────────────────────────────────────
csv = sub.to_csv(index=False).encode("utf-8")
st.download_button(
    label="⬇️ Download data as CSV",
    data=csv,
    file_name=(
        f"classroom_co2_{group_type.replace(' ', '_')}_"
        f"{age_group}_{building.replace(' ', '_')}_{floor_area}m2.csv"
    ),
    mime="text/csv",
)

# ═════════════════════════════════════════════════════════════════════════════
# FOOTER
# ═════════════════════════════════════════════════════════════════════════════
st.divider()
st.caption(
    "CO₂ generation rates: Persily & de Jonge (2017), *Indoor Air*, doi:10.1111/ina.12383.  "
    "Ventilation rates: EN 16798-1:2019, Tables B.6 and B.7.  "
    "Outdoor CO₂ baseline: 420 ppm."
)
