Outcomes

outcomes/ är Treuddens lager för definition och konstruktion av forskningsutfall.

Features beskriver vad som var känt vid observationstillfället.

Outcomes beskriver vad som hände därefter.

Det är denna separation som gör att Treudden kan undersöka om en observerad signal har ett historiskt samband med ett senare utfall.

Ansvar

Outcomes-lagret ansvarar för:

* definition av targets
* target-register
* validering av target-definitioner
* konstruktion av klassificeringsutfall
* konstruktion av regressionsutfall

Det ansvarar inte för:

* analys av signaler
* beräkning av statistik
* modellträning
* tolkning av resultat

Grundmodell

Treudden arbetar principiellt med:

OBSERVATION
    │
    ├── FEATURES
    │      └── information som fanns då
    │
    └── OUTCOME
           └── vad som hände efteråt

Exempel:

2025-01-01
    │
    ├── short_interest = 4.2 %
    ├── insider_net_buy = 1.3 MSEK
    └── eps_surprise = +8 %
             │
             ▼
       framtida utveckling
             │
             ▼
2025-01-21
    return_20d = +6.4 %

Features används som signaler.

return_20d kan användas för att skapa ett outcome.

Target-registret

target_registry.json innehåller de targets som Treudden känner till.

En target beskriver bland annat:

id
return_column
threshold
direction
task
target_column

Exempel:

{
  "id": "return_20d_positive",
  "return_column": "return_20d",
  "threshold": 0.0,
  "direction": "above",
  "task": "classification"
}

Researchspecifikationer refererar till targetens ID i stället för att själva definiera hur targeten ska byggas.

Classification

Classification används när utfallet ska delas upp i klasser.

Exempel:

return_20d > 0

ger:

1 = positiv utveckling
0 = inte positiv utveckling

Threshold och riktning styrs av target-definitionen.

Exempel:

threshold = 0.05
direction = above

betyder att utfallet klassificeras utifrån om avkastningen överstiger 5 %.

Regression

Regression används när det faktiska numeriska utfallet ska behållas.

Exempel:

return_20d = 0.064

behålls som ett numeriskt värde i stället för att omvandlas till 0/1.

Det gör att samma feature kan undersökas mot både:

klassificering

och:

storleken på utfallet

registry.py

Innehåller:

* TargetDefinition
* TargetRegistry
* laddning av target-registret
* uppslagning av targets
* filtrering per task
* validering mot datasetet

Target-registret fungerar som kontrakt mellan outcome-lagret och research-lagret.

targets.py

Innehåller konstruktionen av ett outcome från observerade data.

Huvudfunktionen är:

build_target(
    frame,
    target,
)

För classification skapas ett 0/1-utfall.

För regression returneras den definierade numeriska target-kolumnen.

Separation från features

Det är viktigt att features och outcomes inte blandas ihop.

Exempel:

features:
    blanking.short_interest
    insider.net_buy_30d
    report.eps_surprise
outcomes:
    return_5d
    return_20d
    return_60d

Researchmotorn kan därmed testa samma signal mot flera olika framtida utfall.

Exempel:

signal:
    blanking.short_interest
mot:
    return_5d
    return_20d
    return_60d

Det gör tidsdimensionen till en del av forskningsfrågan snarare än en egenskap hos själva signalen.

Viktig princip

Ett outcome får endast använda information som definierats som framtida relativt observationen.

Features ska representera information vid eller före observationstidpunkten.

Outcomes representerar det som ska mätas efter observationen.

Detta är centralt för att undvika att framtida information råkar användas som signal.

Framtida utveckling

Outcomes kan senare utökas med exempelvis:

absolut avkastning
relativ avkastning
volatilitet
max drawdown
vinst/förlust
rapportutfall

utan att researchmotorn behöver känna till hur respektive outcome konstrueras.

Målet är:

Feature
   +
Target
   ↓
Research
   ↓
Resultat

Outcomes ska alltså vara ett fristående lager för att definiera vad Treudden försöker mäta.
