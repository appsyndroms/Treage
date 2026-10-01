Ja. Jag tycker faktiskt att ARCHITECTURE.md är mer värdefull än ytterligare README-filer när vi börjar få flera lager.

README.md ska förklara vad Treudden är.
ARCHITECTURE.md ska förklara hur delarna hänger ihop och vilka gränser som gäller.

Jag skulle lägga den i roten:

Treudden/
├── README.md
├── ARCHITECTURE.md
├── features/
├── outcomes/
└── research/

Här är första versionen:

Treudden Architecture

Detta dokument beskriver Treuddens arkitektur, ansvarsfördelning och beroenden mellan systemets olika lager.

Målet är att Treudden ska kunna växa från ett researchprojekt till ett generellt forskningsramverk utan att researchmotorn behöver byggas om när nya datakällor tillkommer.

⸻

1. Övergripande arkitektur

Treudden bygger på en enkel kedja:

DATA
  │
  ▼
FEATURES
  │
  ▼
RESEARCH
  │
  ▼
OUTCOMES
  │
  ▼
RESULTS

Mer korrekt är dock att features och outcomes möts i researchmotorn:

                    ┌───────────────┐
                    │     DATA      │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │    FEATURES   │
                    │               │
                    │ What was      │
                    │ observable?   │
                    └───────┬───────┘
                            │
                            │
                            ▼
                    ┌───────────────┐
                    │    RESEARCH   │
                    │               │
                    │ What does the │
                    │ data show?    │
                    └───────┬───────┘
                            │
                            ▲
                            │
                    ┌───────┴───────┐
                    │    OUTCOMES   │
                    │               │
                    │ What happened │
                    │ afterwards?   │
                    └───────────────┘

Research är alltså den centrala konsumenten av både features och outcomes.

⸻

2. Lager

Treudden består av tre centrala logiska lager.

Features

features/

Beskriver observerad information.

Exempel:

blanking.short_interest
insider.net_buy_30d
report.eps_surprise
consensus.revision

Features ska vara oberoende av hur researchen senare analyserar dem.

⸻

Outcomes

outcomes/

Beskriver det framtida utfall som ska undersökas.

Exempel:

return_5d
return_20d
return_60d
volatility_20d

Outcomes ska vara separerade från features för att göra tidsriktningen tydlig.

⸻

Research

research/

Undersöker relationen mellan features och outcomes.

Exempel:

signal:
    blanking.short_interest
target:
    return_20d
analysis:
    regime

Research ska inte behöva känna till vilken datakälla signalen kommer från.

⸻

3. Datakällor

Datakällorna ska ligga utanför researchmotorns logik.

I framtiden kan Treudden exempelvis ha:

data/
├── blanking/
├── insider/
├── reports/
├── consensus/
└── market/

Dessa källor ska transformeras till standardiserade features.

Princip:

Datakälla
    │
    ▼
normalisering
    │
    ▼
Feature
    │
    ▼
SignalRegistry
    │
    ▼
Research

Research ska alltså inte läsa rådata direkt.

⸻

4. SignalRegistry

features/registry.py innehåller definitionerna av Treuddens signaler.

Registret fungerar som ett kontrakt mellan data/feature-lagret och research-lagret.

Research använder:

signal ID

och behöver inte känna till:

rå datakälla
filformat
API
underliggande kolumnnamn

Exempel:

blanking.short_interest
        │
        ▼
SignalRegistry
        │
        ▼
short_interest_pct

Det gör att den interna representationen kan ändras utan att researchspecifikationerna behöver ändras.

⸻

5. TargetRegistry

outcomes/registry.py fyller motsvarande funktion för outcomes.

Research använder:

target ID

i stället för att själv definiera hur targeten ska byggas.

Exempel:

return_20d_positive
        │
        ▼
TargetRegistry
        │
        ▼
return_20d

Target-definitionen bestämmer exempelvis:

* vilken kolumn som används
* threshold
* riktning
* classification eller regression

⸻

6. Researchspecifikationer

Research ska beskrivas deklarativt.

Exempel:

id: blanking_return_20d
signal:
  name: blanking.short_interest
target:
  name: return_20d_positive
analysis:
  type: regime

Det innebär att:

Vad ska undersökas?

kan separeras från:

Hur är analysen implementerad?

Python-koden implementerar analysmetoderna.

YAML-specifikationerna beskriver vilka analyser som ska köras.

⸻

7. Research Engine

research/engine.py är orkestreringslagret.

Den ska:

1. läsa researchspecifikationen
2. hämta signalen
3. hämta targeten
4. välja analysmetod
5. köra analysen
6. returnera resultatet

Den ska inte:

* hämta data från externa källor
* känna till specifika dataleverantörer
* innehålla source-specifik affärslogik

⸻

8. Analysis modules

Analysmetoderna ligger separat från engine.

Exempel:

research/
├── conditional.py
├── derived_metrics.py
├── interaction.py
├── multi_regime.py
├── nested_regime.py
├── regime.py
├── stratified_interaction.py
└── stratified_regime.py

Princip:

Engine
   │
   ├── regime
   ├── conditional
   ├── interaction
   └── ...

Engine väljer analys.

Analysmodulen utför analysen.

⸻

9. Dataset abstraction

Research ska arbeta mot ett standardiserat dataset.

FeatureDataset innehåller:

DataFrame
+
SignalRegistry

Det gör att research inte behöver känna till om data kom från:

JSONL
Parquet
SQL
API

Loadern ansvarar för att skapa rätt representation.

Exempel:

dataset = load_features(
    loader,
    registry,
)

⸻

10. Beroenderiktning

Beroenden ska i huvudsak gå nedifrån och upp mot researchens abstraktioner.

Data sources
     │
     ▼
Features
     │
     ▼
Research
     ▲
     │
Outcomes

Research ska inte importera specifika implementationer från en datakälla.

Undvik exempelvis:

from blanking.api import ...

i research-lagret.

I stället:

from features.registry import ...

Detta är en viktig arkitekturregel.

⸻

11. Treudden och Blankdiss

Blankdiss är en viktig källa till befintliga idéer, dataformat och analysmetoder.

Treudden ska dock inte bli en kopia av Blankdiss.

Principen är:

Blankdiss
    │
    │ erfarenheter
    │ analyser
    │ specs
    ▼
Treudden
    │
    ├── blanking
    ├── insider
    ├── reports
    └── consensus

Det som är generellt bör flyttas mot Treuddens gemensamma lager.

Det som är specifikt för blankning ska fortsätta vara source-specifikt.

⸻

12. Informationskällor

Treuddens namn kommer från tre huvudsakliga informationsområden:

                 TREUDDEN
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
     BLANKING     INSIDER     REPORTS
                              /CONSENSUS

Dessa ska inte vara tre separata researchmotorer.

De ska bli tre olika producenter av features.

Exempel:

Blanking
   │
   └── blanking.short_interest
Insider
   │
   └── insider.net_buy_30d
Reports
   │
   └── report.eps_surprise

Alla kan därefter analyseras av samma researchmotor.

⸻

13. Framtida utbyggnad

När nya datakällor läggs till bör den normala vägen vara:

1. Lägg till datakälla
        │
2. Normalisera data
        │
3. Skapa features
        │
4. Registrera signaler
        │
5. Definiera outcomes vid behov
        │
6. Skapa research-spec
        │
7. Kör befintlig research engine

Om en ny datakälla kräver ändringar i researchmotorn ska det betraktas som en signal om att abstraktionen behöver förbättras.

⸻

14. Vad som ska vara stabilt

Följande gränser bör vara relativt stabila:

Signal ID
Target ID
ResearchSpec
FeatureDataset
Research engine
Analysis interface

Datakällor och enskilda analysmetoder ska däremot kunna förändras utan att hela systemet påverkas.

⸻

15. Kärnprincip

Treuddens arkitektur bygger på separationen:

VAD FANNS?
    │
    ▼
FEATURES
VAD HÄNDE?
    │
    ▼
OUTCOMES
FINNS DET ETT SAMBAND?
    │
    ▼
RESEARCH

Det gör att samma researchmotor kan användas för många olika informationskällor och många olika forskningsfrågor.

Målet är inte att bygga en motor för en viss hypotes.

Målet är att bygga en motor där nya hypoteser kan undersökas utan att systemets grundarkitektur behöver ändras.
