# Classroom CO2 Estimation Tool — Streamlit App

## Quick local run

```bash
pip install -r requirements.txt
streamlit run app.py
```

Your browser opens at `http://localhost:8501`.

---

## Deploy to Streamlit Community Cloud (free)

### Step 1 — Push to GitHub

Create a **public** GitHub repository containing these three files:

```
classroom-co2-tool/
├── app.py
├── requirements.txt
└── README.md
```

```bash
git init
git add app.py requirements.txt README.md
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/classroom-co2-tool.git
git push -u origin main
```

### Step 2 — Deploy on Streamlit Community Cloud

1. Go to **[share.streamlit.io](https://share.streamlit.io)**.
2. Click **Sign in with GitHub** and authorise Streamlit.
3. Click **New app**.
4. Select your repository, branch (`main`), and set main file to `app.py`.
5. Click **Deploy**.

Your app is live at a URL like:
`https://YOUR_USERNAME-classroom-co2-tool-app-XXXXX.streamlit.app`

Share this URL directly — no login needed for viewers.

> Tip: every `git push` to your repository **redeploys the app automatically**.

---

## App features

| Feature | Description |
|---|---|
| 🚦 Status panel | Colour-coded badge for every category × activity combination |
| 📊 Bar chart | Activity on x-axis, category as hue, threshold bands overlaid |
| 🗺️ Heatmap | Category × activity with traffic-light cell colours for CO₂ |
| 📋 Results table | All ventilation and CO₂ values with colour-coded status column |
| ⬇️ CSV download | Download the current selection |
| 📐 Classroom summary | Occupants, volume, density updated live from the floor-area slider |

---

## CO₂ status thresholds

| Status | CO₂ range |
|---|---|
| ✅ Acceptable | < 800 ppm |
| 🟡 Good | 800–1000 ppm |
| ⚠️ Caution | 1000–1500 ppm |
| 🔴 Poor | 1500–2500 ppm |
| 🚨 Very poor | > 2500 ppm |

---

## Classroom parameters

- **Ceiling height**: 2.8 m (fixed)
- **Occupancy density**: 0.5 persons/m² (EN 16798, fixed)
- **Floor area**: 20–100 m² (user-selectable in 5 m² steps)
- **Building types**: Very low polluting, Low polluting, Non low-polluting (EN 16798, Table B.7)
- **Categories**: I, II, III, IV (EN 16798, Table B.6)

---

## Sources

- CO₂ generation rates: Persily & de Jonge (2017), *Indoor Air*, doi:10.1111/ina.12383
- Ventilation rates: EN 16798-1:2019, Tables B.6 and B.7
- Occupancy density: EN 16798-1:2019 (classrooms: 0.5 persons/m²)
