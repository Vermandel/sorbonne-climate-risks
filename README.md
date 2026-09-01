# Climate Risks — Master's in Actuarial Science, Sorbonne University

This repository contains Gauthier Vermandel's transition-risk component: five two-hour sessions. It develops the chain from climate policy and economic activity to emissions, temperature, firms, financial assets and insurance decisions.

## Learning objectives

- Distinguish physical and transition climate risks, and locate this component within the full course.
- Interpret scenarios as conditional pathways rather than forecasts or probabilities.
- Work with a simplified climate model and the DICE integrated assessment model.
- Compare mitigation pathways, quantify parameter uncertainty and discuss the social cost of carbon.
- Discuss the implications and limits of model-based transition scenarios for actuarial and financial risk analysis.

## Course outline

1. Economic foundations of integrated assessment models.
2. Emissions, concentrations and temperature.
3. Climate scenarios and DICE.
4. Parametric uncertainty.
5. Optimal climate policy and the social cost of carbon.

## Syllabus

The component syllabus, including the calendar and assessment format, is
available in `Syllabus_Risques_Climatiques.pdf`.

## Slide decks

Each session is available in two synchronised formats:

- `SessionX_compact.pdf` is the student-facing reference version. The course
  website links to this format; the legacy `SessionX.pdf` files remain compact
  aliases so that existing links keep working.
- `SessionX_extended.pdf` is the presentation version. Its bullet points are
  revealed one at a time and the newly revealed point is highlighted.

## Installation and practical sessions

Python 3.12 and Jupyter are required. Create the environment locally, outside
the Dropbox folder:

```bash
python3.12 -m venv ~/.venvs/su-risques-climatiques
source ~/.venvs/su-risques-climatiques/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

From the same project root, then run:

```bash
jupyter notebook
```

Open the exercise notebooks in `Session1/` through `Session5/`, in order.
Solutions are published automatically fifteen minutes before the end of each
session. Download each notebook together with the files located beside it:

- `Session1/TP1_sujet.ipynb` uses `Session1/OptimalGrowth.py`;
- `Session2/TP2_sujet.ipynb` uses `Session2/climate_models.py` and
  `Session2/Notebook_ClimateModels_SSP_data.csv`;
- `Session3/TP3_basics.ipynb` introduces DICE before the scenario exercises
  in `Session3/TP3_sujet.ipynb`;
- `Session4/TP4_sujet.ipynb` covers parametric uncertainty;
- `Session5/TP5_sujet.ipynb` covers optimisation and the social cost of carbon,
  with `Session5/TP5_bonus_sujet.ipynb` on discounting and tipping points;
- for Sessions 3 through 5, `DICE.py` is located directly in each session
  folder and must be downloaded with the notebook.

Other shared data are kept in `data/`.

Never create, commit, or synchronise a virtual environment in this teaching
repository: `.venv/`, `venv/`, and `env/` are excluded by `.gitignore`.

## Scheduled solution publication (PSC)

The PSC procedure stores each forthcoming solution in encrypted form, then a
GitHub Action decrypts and publishes it at the time specified in
`publication/releases.json`. It runs every five minutes and can also be started
manually from the Actions tab.

To prepare a solution for another course:

1. encrypt it with
   `scripts/prepare_correction.sh path/to/solution.ipynb publication/encrypted/solution.ipynb.gpg`;
2. add its identifier, timezone-aware ISO-8601 release time, encrypted path,
   and public target path to the manifest;
3. commit only the `.gpg` archive, the manifest, and the course webpage —
   never the plaintext solution before its release time;
4. give the website button the `psc-correction` class and a `data-release-at`
   attribute containing exactly the same time.

The public key `publication/psc-public-key.asc` is used to prepare the
archives. The private key is held only in the GitHub secret `PSC_PRIVATE_KEY`.

## References

- GIEC (2021), *AR6 Working Group I*.
- GIEC (2023), *AR6 Synthesis Report*.
- NGFS (2024), *NGFS Climate Scenarios for Central Banks and Supervisors*.
- O'Neill et al. (2017), *The roads ahead: Narratives for shared socioeconomic pathways*.
- Nordhaus (2017), *Revisiting the social cost of carbon*.
- TCFD (2017), *Recommendations of the Task Force on Climate-related Financial Disclosures*.
- IAIS (2021), *Application Paper on the Supervision of Climate-related Risks*.
- McNeil, Frey et Embrechts (2015), *Quantitative Risk Management*.
