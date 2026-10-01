# Treudden

Treudden är ett forskningsramverk för att undersöka om olika informationskällor tillsammans innehåller historiskt användbar information om framtida marknadsutfall\.

Namnet Treudden kommer från de tre huvudsakliga informationsområden som systemet ska kunna kombinera:

1. **Blankning**
2. **Insiderdata**
3. **Rapporter och konsensus**

Treudden ska inte vara ett system som i förväg antar vilken av dessa informationskällor som är viktigast\.

I stället ska systemet kunna ställa frågor av typen:

> Finns det historiskt observerbara samband mellan en eller flera signaler och ett definierat framtida utfall?

## Grundidé

Treudden separerar fyra saker:

```text
DATA
  │
  ▼
FEATURES / SIGNALS
  │
  ▼
RESEARCH
  │
  ▼
OUTCOMES
```

Det är viktigt att signalerna och utfallet hålls separerade\.

En signal beskriver vad som var känt eller observerbart vid en viss tidpunkt\.

Ett outcome beskriver vad som därefter faktiskt hände\.

Research\-lagret undersöker relationen mellan dem\.

Det innebär exempelvis att samma framtida avkastningsutfall kan användas för att undersöka:

- blankningssignaler
- insidertransaktioner
- rapportdata
- konsensusförändringar
- kombinationer av ovanstående

## Arkitektur

Den nuvarande strukturen är:

```text
Treudden/
│
├── features/
│   ├── dataset.py
│   ├── registry.py
│   └── signal_registry.json
│
├── outcomes/
│   ├── registry.py
│   ├── targets.py
│   └── target_registry.json
│
├── research/
│   ├── analysis_utils.py
│   ├── bootstrap.py
│   ├── cache.py
│   ├── conditional.py
│   ├── derived_metrics.py
│   ├── engine.py
│   ├── evaluator.py
│   ├── interaction.py
│   ├── multi_regime.py
│   ├── nested_regime.py
│   ├── regime.py
│   ├── research_registry.json
│   ├── runner.py
│   ├── session.py
│   ├── signals.py
│   ├── spec.py
│   ├── stratified_interaction.py
│   ├── stratified_regime.py
│   ├── walk_forward.py
│   └── walk_forward_registry.json
│
└── README.md
```

Strukturen kommer att växa när datakällorna kopplas in\.

## Features

`features/` definierar hur observerbara signaler representeras i Treudden\.

En signal har bland annat:

- ett stabilt ID
- en källa
- en feature\-kolumn
- en typ
- en beskrivning

Signaldefinitionerna ligger i:

```text
features/signal_registry.json
```

Kod som behöver använda en signal ska inte behöva känna till hur signalen ursprungligen producerades\.

Det är en central princip\.

Exempel:

```text
blanking.short_interest
insider.net_buy_30d
report.eps_surprise
consensus.eps_revision_30d
market.return_20d
```

Researchmotorn ska kunna använda dessa på samma sätt\.

## Outcomes

`outcomes/` beskriver de framtida utfall som research ska mäta\.

Ett outcome ska vara oberoende av den signal som undersöks\.

Exempel:

```text
future return > 5 %
future return > 10 %
future return < -5 %
future volatility
```

Targets definieras i:

```text
outcomes/target_registry.json
```

Det gör att samma outcome kan användas av flera helt olika forskningsfrågor\.

## Research

`research/` är Treuddens centrala forskningsmotor\.

Den är deklarativ\.

En forskningsfråga uttrycks som en `ResearchSpec`, normalt i YAML, exempelvis:

```yaml
id: example_signal

question: >
  Har den övre 10 procenten av signalen
  högre framtida avkastning?

signals:
  - name: example.signal
    direction: upper
    bins:
      - 0.10

targets:
  - return_20d_positive

analysis:
  type: tail

mode: scan
```

Researchmotorn bestämmer sedan hur experimentet ska genomföras\.

Det innebär att själva analysmotorn inte behöver innehålla hårdkodade definitioner av en viss datakälla\.

## Research modes

Research kan köras i olika lägen\.

Exempelvis:

- `scan` – bredare sökning efter historiska samband
- `deep` – mer detaljerad analys av en identifierad hypotes

De tillåtna lägena och analysformerna styrs av research\-registret\.

## Analysformer

Researchmotorn innehåller stöd för bland annat:

- tail analysis
- regime comparison
- nested regime comparison
- multi\-regime comparison
- conditional regime comparison
- interaction analysis
- stratified regime comparison
- stratified interaction
- bootstrap
- walk\-forward analysis

Det betyder att Treudden inte bara kan fråga om en enskild signal fungerar\.

Den kan också undersöka frågor som:

```text
Signal A
    +
Signal B
    ↓
framtida outcome
```

eller:

```text
Signal A
    ↓
olika regimer
    ↓
Signal B
    ↓
framtida outcome
```

## Researchspecifikationer

`research/spec.py` definierar den gemensamma modellen för en forskningsfråga\.

En `ResearchSpec` innehåller bland annat:

- `id`
- `question`
- `signals`
- `targets`
- `analysis`
- `mode`
- `windows`
- `splits`
- `metadata`

Specifikationen valideras mot registren innan research körs\.

Det gör att ogiltiga kombinationer kan stoppas innan själva analysen startar\.

## Runner

`research/runner.py` ansvarar för orkestreringen\.

Runnern:

1. hittar researchspecifikationer
2. läser in dem
3. validerar dem
4. skapar en research\-session
5. bygger cache
6. kör varje spec
7. returnerar resultaten

Runnern ska inte innehålla specifik kunskap om exempelvis blankning eller insiderdata\.

## Viktig arkitekturprincip

Treudden ska vara **generellt medan datakällorna är specifika**\.

Det innebär:

```text
             ┌── Blankning
             │
DATA ────────┼── Insider
             │
             ├── Rapporter
             │
             ├── Konsensus
             │
             └── Marknadsdata
                    │
                    ▼
                 FEATURES
                    │
                    ▼
              RESEARCH ENGINE
                    │
                    ▼
                 OUTCOMES
```

Researchmotorn ska inte behöva veta varifrån en signal kommer\.

Det är registren som kopplar samman signal\-ID:n med konkreta feature\-kolumner\.

## Förhållandet till Blankdiss

Treudden bygger vidare på erfarenheterna från Blankdiss\.

Blankdiss har redan visat hur man kan bygga:

```text
rådata
  ↓
features
  ↓
research
  ↓
historiska outcomes
  ↓
prospektiv verifiering
```

Treudden ska däremot inte bli en kopia av Blankdiss\.

Det som ska återanvändas är framför allt:

- researchmotorns generella principer
- deklarativa researchspecifikationer
- signalregister
- target/outcome\-register
- cache
- experimenthantering
- walk\-forward/verifiering
- separation mellan observation och outcome

De faktiska Blankdiss\-featuresen ska inte automatiskt flyttas över\.

## Framtida datalager

När datakällorna kopplas in är den tänkta riktningen:

```text
data/
├── raw/
│   ├── blanking/
│   ├── insider/
│   ├── reports/
│   ├── consensus/
│   └── market/
│
└── processed/
    ├── features/
    ├── outcomes/
    └── research/
```

Detta är en framtida struktur och ska inte betraktas som implementerad förrän katalogerna faktiskt finns\.

## Forskningsprincip

Treudden ska i första hand vara ett system för att **hitta och testa information**, inte ett system som försöker bevisa en förutbestämd idé\.

Exempel:

```text
Hypotes:
"Stor ökning av blankning föregår kursfall."

Treudden:
1. definiera signal
2. definiera outcome
3. definiera tidsfönster
4. kör research
5. utvärdera resultat
6. kontrollera stabilitet
7. prospektivt verifiera
```

Samma process ska kunna användas för alla informationskällor\.

## Status

Projektet är under utveckling\.

Den centrala researchmotorn är redan implementerad i `research/`\.

`features/` och `outcomes/` innehåller den gemensamma abstraheringen som krävs för att koppla researchmotorn till framtida datakällor\.

Nästa större steg är att koppla in verkliga datakällor och bygga Treuddens generella featurelager\.
