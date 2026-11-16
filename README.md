# Process Capability & SPC Studio

Industrial statistical process control dashboard by **Sepp Sina**.

## Start
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy
Deploy this app on [Streamlit Community Cloud](https://share.streamlit.io/) by selecting this repository and setting the app file to `app.py`.

Includes: I-MR and Xbar-R charts, subgroup diagnostics, Cp/Cpk and Pp/Ppk, distribution, segment comparisons, CSV/XLSX upload, demo dataset, and downloadable PDF/CSV reports.

**Important:** Demo data is synthetic. Capability indices are descriptive; do not declare a process capable solely from a high Cpk when control chart signals indicate instability. For Xbar-R charts use subgroup size 2–10. The control constants supplied are standard tabulated values. For I-MR, the moving range is computed between successive observations. Limits are estimated from the complete selected dataset; for formal phase-II monitoring, freeze validated baseline limits separately.

CSV upload: include a numeric measurement column (`value`, `measurement`, `diameter`, etc.). Optional columns: `subgroup`, `shift`, `cavity`, `station`, `date`. Use subgroup labels for Xbar-R analysis. Input specification limits in sidebar.

This software is for engineering analysis and must be validated against approved reference calculations before regulated or safety-critical use.
