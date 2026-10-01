# Treudden
Ja. Jag har nu tittat på den faktiska nuvarande Blankdiss-strukturen, inte bara README:n. Det viktigaste jag ser är att Blankdiss redan har byggt fram flera delar som egentligen hör hemma i Treudden.

Framför allt finns ett tydligt separationsmönster: data → features → forskning → kandidater → prospektiv utvärdering → verifiering. 

Jag skulle därför göra Treudden till en renare generalisering av Blankdiss, inte en kopia.

Några konkreta fynd:

* data/processed/analysis/ innehåller nu 28 feature-chunks, totalt 208 594 feature-rader, plus metadata och QC.
* Feature-datasetet innehåller redan pris, blankning, marknad och sektor, inklusive forward returns på 1/3/5/10/20/60 handelsdagar.
* Det finns ett separat short_cycles-dataset.
* data/processed/ml/ innehåller bl.a. ml_results.jsonl, economic_results.json, latest_run.json samt research/runs.
* ml/research/ är redan en ganska komplett deklarativ forskningsmotor med specs, sessions, cache, signals, engine, runner, reporting, verification och walk-forward.
* analysis/ innehåller mycket som är specifikt för att bygga just Blankdiss-featuret, och det ska inte kopieras rakt av till Treudden.

Det betyder att jag skulle börja Treudden ungefär så här:

Treudden/
│
├── research/
│   ├── engine/
│   ├── specs/
│   ├── candidates/
│   ├── evaluation/
│   └── verification/
│
├── features/
│   ├── builders/
│   ├── registry/
│   ├── dataset/
│   └── qc/
│
├── models/
│   ├── conventional/
│   ├── experiments/
│   └── ai/
│
├── outcomes/
│   ├── returns/
│   ├── targets/
│   └── events/
│
├── data/
│   ├── raw/
│   │   ├── blanking/
│   │   ├── insider/
│   │   ├── reports/
│   │   ├── consensus/
│   │   └── market/
│   │
│   └── processed/
│       ├── features/
│       ├── outcomes/
│       └── research/
│
├── tests/
│
└── README.md

Det jag vill lyfta från Blankdiss

1. Research Engine — nästan direkt

Det här är den tydligaste kandidaten. Den deklarativa modellen, research specs, sessions, caching, scan/deep, candidates, evaluation och verification är precis den typ av generell motor Treudden behöver.

2. Feature-lagret — konceptet och mycket av infrastrukturen

Inte feature_fi.py som sådan, utan principen:

olika datakällor → standardiserade features → gemensamt dataset

Blankdiss har redan visat att detta fungerar med 208 594 rader och 28 chunks. Metadata innehåller dessutom source fingerprint, featurekolumner, chunkstorlek och datakvalitet. Det är väldigt värdefullt att ta med.

3. Historiska outcomes

Det här är ännu viktigare i Treudden. Blankdiss har redan forward_return_1d, 3d, 5d, 10d, 20d, 60d samt relativa marknads-/sektorutfall.

I Treudden ska outcomes däremot vara oberoende av signalen.

Det är en viktig arkitekturprincip:

          FEATURES
              │
              ▼
       Research Engine
              │
              ▼
          OUTCOMES

Inte:

blankning → blanknings-outcome

Då kan samma outcome användas för:

blankning
insider
rapport
konsensus
kombinationer

4. AI/ML

Jag skulle lyfta själva experimentramverket och modellhanteringen, men inte låsa Treudden till de modeller Blankdiss råkar använda idag.

Treudden ska kunna fråga:

“Finns det någon kombination av dessa features som historiskt innehåller information?”

utan att arkitekturen redan antar vilken modell som ska hitta den.

⸻

Och data-katalogen säger något viktigt

Jag skulle inte flytta över de 28 features_*.jsonl-filerna som de är.

De är resultatet av Blankdiss nuvarande featuremodell. De innehåller exempelvis:

short_interest_pct
active_holders
short_interest_delta_pp
short_interest_acceleration_pp
price_return_5d
price_return_20d
price_volatility_20d
sector_return_20d
market_return_20d
forward_return_20d
...

Det som ska flyttas är modellen för hur datasetet byggs och beskrivs, inte nödvändigtvis själva filerna.

Treudden ska istället kunna producera något i stil med:

feature dataset
──────────────────────────────
market.*
blanking.*
insider.*
report.*
consensus.*
sector.*
derived.*

Och då kan en Treudden-rad i framtiden faktiskt beskriva samma observation ur alla tre uddarna.

Exempel:

2026-10-01
SE...
    blanking.short_interest = 7.4
    insider.net_buy_30d = +...
    report.eps_surprise = +...
    consensus.eps_revision_30d = +...
    market.return_20d = ...
    sector.return_20d = ...

Det är den stora arkitekturella vinsten.

Blankdiss har redan byggt första udden och mycket av infrastrukturen. Treudden blir platsen där vi gör infrastrukturen generell.
