Features

features/ är Treuddens lager för standardiserade forskningssignaler.

Syftet är att göra olika datakällor användbara på ett gemensamt sätt för researchmotorn.

Ansvar

Features-lagret ansvarar för:

* signaldefinitioner
* signalregister
* validering av feature-dataset
* åtkomst till signaler
* representation av ett feature-dataset

Det ansvarar inte för:

* researchanalys
* targets
* modellträning
* datakällornas ursprungliga API-format

Signalregister

signal_registry.json är katalogen över de signaler som Treudden känner till.

En signal definieras bland annat av:

id
source
column
type
description

Exempel:

{
  "id": "blanking.short_interest",
  "source": "blanking",
  "column": "short_interest_pct",
  "type": "numeric",
  "description": "Short interest som andel av aktier."
}

Researchkod ska använda signalens ID och inte behöva känna till den underliggande kolumnens namn.

Signal → feature

Relationen är:

signal ID
    │
    ▼
SignalRegistry
    │
    ▼
feature column
    │
    ▼
DataFrame

Detta gör att researchmotorn kan vara oberoende av datakällan.

registry.py

Innehåller:

* SignalDefinition
* SignalRegistry
* laddning av signalregistret
* uppslagning av signaler
* filtrering per källa
* validering mot ett DataFrame

dataset.py

Innehåller FeatureDataset.

FeatureDataset består av:

DataFrame
+
SignalRegistry

Det är medvetet en enkel representation.

Research-lagret ska inte behöva veta om datasetet ursprungligen kom från:

* JSONL
* Parquet
* databas
* API
* annan källa

Det hanteras av ett loader-interface.

dataset = load_features(
    loader,
    registry,
)

Viktig princip

Features ska beskriva information som var observerbar vid observationstillfället.

Framtida utfall ska inte byggas in i signalerna.

Exempel:

Rätt:
insider.net_buy_30d
blanking.short_interest
report.eps_surprise
Fel:
insider.predicts_return_20d
blanking.future_loss

Det framtida utfallet hör hemma i outcomes/.

Framtida datakällor

Treudden ska kunna bygga features från exempelvis:

blanking/
insider/
reports/
consensus/
market/

Dessa ska sedan normaliseras till ett gemensamt feature-dataset.

Exempel:

snapshot_date
instrument
market.*
sector.*
blanking.*
insider.*
report.*
consensus.*
derived.*

Det innebär att en observation i framtiden kan beskriva flera informationskällor samtidigt.

Vad features-lagret inte ska göra

Features ska inte avgöra om en signal är bra eller dålig.

Det är researchlagrets uppgift att testa detta.

Features-lagret ska endast svara på:

Vilken observerad information fanns för den här observationen?
