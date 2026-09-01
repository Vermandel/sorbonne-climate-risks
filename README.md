# Risques climatiques — Master 2 Actuariat, Sorbonne Université

This repository contains Gauthier Vermandel's transition-risk component: five two-hour sessions. It develops the chain from climate policy and economic activity to emissions, temperature, firms, financial assets and insurance decisions.

## Objectifs

- Distinguish physical and transition climate risks, and locate this component within the full course.
- Interpret scenarios as conditional pathways rather than forecasts or probabilities.
- Work with a simplified climate model and the DICE integrated assessment model.
- Compare mitigation pathways, quantify parameter uncertainty and discuss the social cost of carbon.
- Discuss the implications and limits of model-based transition scenarios for actuarial and financial risk analysis.

## Plan

1. Economic foundations of integrated assessment models.
2. Emissions, concentrations and temperature.
3. Climate scenarios and DICE.
4. Parametric uncertainty.
5. Optimal climate policy and the social cost of carbon.

## Syllabus

The component syllabus, including the calendar and assessment format, is
available in `Syllabus_Risques_Climatiques.pdf`.

## Installation et TP

Python 3.12 et Jupyter sont requis. Créer l'environnement localement, hors du
dossier Dropbox :

```bash
python3.12 -m venv ~/.venvs/su-risques-climatiques
source ~/.venvs/su-risques-climatiques/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Depuis cette même racine, lancer ensuite :

```bash
jupyter notebook
```

Ouvrir les sujets dans `Session1/` à `Session5/`, dans l'ordre. Les corrigés
sont publiés automatiquement quinze minutes avant la fin de chaque séance.
Chaque notebook doit être téléchargé avec les fichiers placés à côté de lui :

- `Session1/TP1_sujet.ipynb` utilise `Session1/OptimalGrowth.py` ;
- `Session2/TP2_sujet.ipynb` utilise `Session2/climate_models.py` et
  `Session2/Notebook_ClimateModels_SSP_data.csv` ;
- `Session3/TP3_basics.ipynb` introduit DICE avant les exercices de scénarios
  de `Session3/TP3_sujet.ipynb` ;
- `Session4/TP4_sujet.ipynb` porte sur l'incertitude paramétrique ;
- `Session5/TP5_sujet.ipynb` présente l'optimisation et le coût social du
  carbone, avec `Session5/TP5_bonus_sujet.ipynb` sur l'actualisation et les
  tipping points ;
- pour les Sessions 3 à 5, `DICE.py` se trouve directement dans le dossier de
  la séance et doit être téléchargé avec le notebook.

Les autres données communes sont conservées dans `data/`.

Ne jamais créer, versionner ou synchroniser un environnement virtuel dans ce
dépôt pédagogique : `.venv/`, `venv/` et `env/` sont exclus par `.gitignore`.

## Publication synchronisée des corrigés (PSC)

La procédure PSC conserve chaque futur corrigé sous forme chiffrée, puis une
GitHub Action le déchiffre et le publie à la date indiquée dans
`publication/releases.json`. Elle s'exécute toutes les cinq minutes et peut
aussi être lancée manuellement depuis l'onglet Actions.

Pour préparer un corrigé d'un autre cours :

1. le chiffrer avec
   `scripts/prepare_correction.sh chemin/corrige.ipynb publication/encrypted/corrige.ipynb.gpg` ;
2. ajouter au manifeste son identifiant, son heure ISO-8601 avec fuseau, le
   chemin chiffré et le chemin public cible ;
3. versionner uniquement l'archive `.gpg`, le manifeste et la page du cours —
   jamais le corrigé en clair avant l'échéance ;
4. donner au bouton du site la classe `psc-correction` et un attribut
   `data-release-at` contenant exactement la même heure.

La clé publique `publication/psc-public-key.asc` prépare les archives. La clé
privée n'est présente que dans le secret GitHub `PSC_PRIVATE_KEY`.

## Références

- GIEC (2021), *AR6 Working Group I*.
- GIEC (2023), *AR6 Synthesis Report*.
- NGFS (2024), *NGFS Climate Scenarios for Central Banks and Supervisors*.
- O'Neill et al. (2017), *The roads ahead: Narratives for shared socioeconomic pathways*.
- Nordhaus (2017), *Revisiting the social cost of carbon*.
- TCFD (2017), *Recommendations of the Task Force on Climate-related Financial Disclosures*.
- IAIS (2021), *Application Paper on the Supervision of Climate-related Risks*.
- McNeil, Frey et Embrechts (2015), *Quantitative Risk Management*.
