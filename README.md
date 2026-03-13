# Mass Spectrometry Experiment Planner (Front-End)

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://ms-experiment.streamlit.app/)

This repository contains a Streamlit web app to design 96‑well plates, generate MS acquisition lists, and create SDRF and Skyline annotation files for DIA, DDA, SRM, and PRM experiments.

### Key Features

- **Plate design**: Define plate layouts, cohorts, pools, controls, and empty wells.
- **Sample order generation**: Build randomized or fixed injection tables for Xcalibur (including QC and wash injections).
- **Evosep/Chronos export**: Create Evosep-compatible CSV/XML files for Chronos runs.
- **SDRF builder**: Generate SDRF files with sample/assay annotations and acquisition parameters.
- **Skyline annotations**: Produce CSV annotations for Skyline based on SDRF characteristics.

### Running Locally

1. **Create and activate a virtual environment (optional but recommended)**  
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```

2. **Install dependencies**  
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the app**  
   From the project root:
   ```bash
   streamlit run web.py
   ```

4. **Open in browser**  
   Streamlit will show a local URL (e.g. `http://localhost:8501`). Open it to use the app.

### Basic Usage

- **Intro tab**: Review project‑level information and guidance.
- **Plate Design tab**:
  - Enter the main cohort/sample name and plate ID in the sidebar.
  - Use the text area to annotate extra cohorts/pools/controls.  
    - Format each line as `Label;Position`, e.g. `Pool;A7` or `Cohort_2;RowD` or `Cohort_2;Col8`.  
    - You can also specify multiple wells in one line, e.g. `Sample1;A1,A3,A5`.
  - The plate layout and label counts are displayed as plots.
- **Xcalibur tab**: Configure injection volume, method files, QC/wash injections, and export the randomized sample order CSV.
- **Chronos (Evosep) tab**: Configure Evosep/Chronos options and download CSV/XML (and copy XML to clipboard).
- **SDRF tab**: Build and download the SDRF `.tsv` file for downstream repositories/tools.
- **Skyline tab**: Use the generated or uploaded SDRF to export a Skyline annotation CSV.

### Notes

- The app expects a 96‑well plate layout (8 rows A–H × 12 columns 1–12).
- `EMPTY` wells in the Plate Design tab will be excluded from later steps (sample order, SDRF, etc.).
- OpenAI/agent features in the Plate Design tab are optional and require an API key and the `hypha-rpc` extra dependency.

### Development TODOs

- [ ] Refine SDRF defaults (sample prep, Hamilton, etc.).
- [ ] Improve download packaging (e.g. optional ZIP including plots and tables).
- [ ] Expand documentation/examples for typical DIA and SRM/PRM workflows.
