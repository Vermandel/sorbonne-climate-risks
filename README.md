# Risques climatiques — Master 2 Actuariat, Sorbonne Université

Ce dépôt contient le volet consacré au risque de transition de Gauthier Vermandel : cinq séances de deux heures. Il développe la chaîne qui relie les politiques climatiques et l'activité économique aux émissions, à la température, aux entreprises, aux actifs financiers et aux décisions d'assurance.

## Objectifs pédagogiques

- Distinguer les risques climatiques physiques et de transition, et situer ce volet dans le cours complet.
- Interpréter les scénarios comme des trajectoires conditionnelles plutôt que comme des prévisions ou des probabilités.
- Utiliser un modèle climatique simplifié et le modèle intégré d'évaluation DICE.
- Comparer des trajectoires d'atténuation, quantifier l'incertitude des paramètres et discuter le coût social du carbone.
- Discuter les implications et les limites des scénarios de transition issus de modèles pour l'analyse des risques actuariels et financiers.

## Plan du cours

1. Fondements économiques des modèles intégrés d'évaluation.
2. Émissions, concentrations et température.
3. Scénarios climatiques et DICE.
4. Incertitude paramétrique.
5. Politique climatique optimale et coût social du carbone.

## Syllabus

Le syllabus du volet, incluant le calendrier et les modalités d'évaluation, est
disponible dans `Syllabus_Risques_Climatiques.pdf`.

## Diaporamas

Chaque séance est disponible dans deux formats synchronisés :

- `slides/SessionX_compact.pdf` est la version de référence destinée aux étudiant·es.
  La page du cours renvoie directement vers ce format.
- `slides/SessionX_extended.pdf` est la version de présentation. Ses puces sont
  révélées une à une et la puce nouvellement révélée est mise en évidence.

- Séance 1 — [version compacte](Session1/slides/Session1_compact.pdf) · [version étendue](Session1/slides/Session1_extended.pdf)
- Séance 2 — [version compacte](Session2/slides/Session2_compact.pdf) · [version étendue](Session2/slides/Session2_extended.pdf)
- Séance 3 — [version compacte](Session3/slides/Session3_compact.pdf) · [version étendue](Session3/slides/Session3_extended.pdf)
- Séance 4 — [version compacte](Session4/slides/Session4_compact.pdf) · [version étendue](Session4/slides/Session4_extended.pdf)
- Séance 5 — [version compacte](Session5/slides/Session5_compact.pdf) · [version étendue](Session5/slides/Session5_extended.pdf)

## Installation et travaux pratiques

Python 3.12 et Jupyter sont requis. Créez l'environnement localement, hors du
dossier Dropbox :

```bash
python3.12 -m venv ~/.venvs/su-risques-climatiques
source ~/.venvs/su-risques-climatiques/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Depuis cette même racine, lancez ensuite :

```bash
jupyter notebook
```

Ouvrez les sujets de TP dans `Session1/codes/` à `Session5/codes/`, dans
l'ordre. Chaque séance est autonome :

- `TPX_sujet.ipynb` est le sujet ;
- `correction/TPX_corrige.ipynb` est le corrigé publié lorsque l'embargo est
  levé ;
- `toolbox/` contient les modules Python développés pour le cours ;
- `data/` contient les données CSV nécessaires.

Le préambule commun aux notebooks installe uniquement les paquets pip absents,
puis vérifie les fichiers locaux. Il ne télécharge pas de module de cours.

Ne créez, ne versionnez et ne synchronisez jamais d'environnement virtuel dans
ce dépôt pédagogique : `.venv/`, `venv/` et `env/` sont exclus par `.gitignore`.

## Publication synchronisée des corrigés (PSC)

La procédure PSC conserve chaque futur corrigé sous forme chiffrée, puis une
GitHub Action le déchiffre et le publie à la date indiquée dans
`publication/releases.json`. Elle s'exécute toutes les cinq minutes et peut
aussi être lancée manuellement depuis l'onglet Actions.

Pour préparer un corrigé d'un autre cours :

1. le chiffrer avec
   `scripts/prepare_correction.sh path/to/solution.ipynb publication/encrypted/solution.ipynb.gpg`;
2. ajouter au manifeste son identifiant, son heure ISO-8601 avec fuseau, le
   chemin chiffré et le chemin public cible ;
3. versionner uniquement l'archive `.gpg`, le manifeste et la page du cours —
   jamais le corrigé en clair avant l'échéance ;
4. donner au bouton du site la classe `psc-correction` et un attribut
   `data-release-at` contenant exactement la même heure.

La clé publique `publication/psc-public-key.asc` sert à préparer les archives.
La clé privée n'est présente que dans le secret GitHub `PSC_PRIVATE_KEY`.

## Références

- GIEC (2021), *AR6 Working Group I*.
- GIEC (2023), *AR6 Synthesis Report*.
- NGFS (2024), *NGFS Climate Scenarios for Central Banks and Supervisors*.
- O'Neill et al. (2017), *The roads ahead: Narratives for shared socioeconomic pathways*.
- Nordhaus (2017), *Revisiting the social cost of carbon*.
- TCFD (2017), *Recommendations of the Task Force on Climate-related Financial Disclosures*.
- IAIS (2021), *Application Paper on the Supervision of Climate-related Risks*.
- McNeil, Frey et Embrechts (2015), *Quantitative Risk Management*.
