Nästa fil: research/README.md.

Research

research/ är Treuddens forskningsmotor.

Här kombineras features och outcomes för att undersöka historiska samband mellan observerad information och framtida utfall.

Research-lagret ska vara så generellt som möjligt. Det ska inte känna till om en signal kommer från blankning, insiderdata, rapporter eller någon annan datakälla.

Grundmodell

Research tar emot:

FEATURES
    +
OUTCOME
    +
RESEARCH SPEC
    │
    ▼
RESEARCH ENGINE
    │
    ▼
RESULTAT

En research-spec beskriver vad som ska undersökas.

Motorn ansvarar för hur undersökningen körs.

Research-specifikationer

Research definieras deklarativt i YAML-filer under:

research/specs/

En spec kan exempelvis beskriva:

id: blanking_return_20d
signal:
  name: blanking.short_interest
target:
  name: return_20d_positive
analysis:
  type: regime

Tanken är att en ny forskningsfråga i första hand ska kunna skapas genom konfiguration i stället för ny Python-kod.

ResearchSpec

En research-spec innehåller den information som behövs för att beskriva en körning.

Den kan bland annat ange:

signal
target
analysis
windows
parameters
mode

Den exakta strukturen styrs av Treuddens research-modeller.

Research runner

runner.py fungerar som ingångspunkt för att köra research-specifikationer.

Runnern ansvarar bland annat för att:

1. hitta specs
2. läsa in registry-definitioner
3. skapa research-session
4. köra valda specs
5. samla resultaten

Research runnern ska däremot inte innehålla den statistiska analyslogiken.

Research engine

engine.py orkestrerar själva analysen.

Den kopplar samman:

Signal
   │
   ▼
FeatureDataset
   │
   ├──────────────┐
   │              │
   ▼              ▼
Target        Analysis
   │              │
   └──────┬───────┘
          ▼
       Resultat

Motorn ska kunna använda samma grundstruktur oavsett vilken informationskälla signalen kommer från.

Analysmoduler

Research innehåller separata moduler för olika typer av analyser.

Exempel är:

conditional
derived_metrics
interaction
multi_regime
nested_regime
regime
stratified_interaction
stratified_regime

Varje analys ska ha ett tydligt avgränsat ansvar.

Det gör att nya analystyper kan läggas till utan att researchmotorns grundstruktur behöver byggas om.

Signaler

signals.py innehåller gemensam hantering av researchsignaler.

En signal hämtas genom sitt ID från SignalRegistry.

Exempel:

build_signal(
    frame,
    signal_name,
    registry,
)

Researchkoden behöver därmed inte hårdkoda feature-kolumnen.

Tail-analyser

Research kan dela in observationer efter signalens relativa nivå.

Exempel:

alla observationer
        │
        ├── högsta 10 %
        ├── nästa 10 %
        ├── ...
        └── lägsta 10 %

Det gör det möjligt att undersöka om ett samband förändras beroende på signalens nivå.

Regimer

Research kan även undersöka om samband varierar mellan olika marknads- eller observationsregimer.

Det är viktigt eftersom ett samband som ser stabilt ut totalt kan bete sig annorlunda i olika delar av datamängden.

Interaktioner

Research kan undersöka flera signaler tillsammans.

Exempel:

signal A
    +
signal B
    │
    ▼
framtida outcome

Det gör det möjligt att undersöka om kombinationen av två informationskällor innehåller information som inte syns när signalerna analyseras var för sig.

Det är särskilt relevant för Treuddens övergripande idé:

Blankning
    +
Insiderdata
    +
Rapporter / konsensus

Research är källoberoende

Researchmotorn ska inte ha speciallogik som:

if source == "blanking"

eller:

if source == "insider"

I stället ska den arbeta mot generella signaldefinitioner.

Det innebär att samma analys kan användas för:

blanking.short_interest
insider.net_buy_30d
report.eps_surprise
consensus.revision

utan att analysmotorn behöver ändras.

Research och Blankdiss

Blankdiss är en viktig föregångare till Treudden.

Treudden ska kunna återanvända idéer, analysmetoder och forskningsspecifikationer från Blankdiss där de passar.

Skillnaden är att Treudden ska abstrahera bort den specifika datakällan.

Principen är:

Blankdiss
    │
    ├── signaler
    ├── analyser
    └── specs
           │
           ▼
       Treudden
           │
    ┌──────┼──────┐
    ▼      ▼      ▼
blanking insider reports

Treudden ska alltså inte kopiera Blankdiss blint.

Det som är generellt hör hemma i Treudden.

Det som är specifikt för en viss datakälla ska ligga närmare datakällan.

Research modes

Research kan köras i olika lägen.

Ett viktigt exempel är:

scan

för bredare undersökningar.

Ett annat är:

deep

för mer detaljerad analys.

Modes ska styra hur mycket research som körs, inte ändra betydelsen av själva signalerna eller targets.

Forskningsprincip

Treudden ska inte utgå från att en viss signal måste fungera.

Exempel på en legitim forskningsfråga:

Har hög short interest historiskt varit förknippad med ett annat framtida utfall än låg short interest?

Samma fråga kan sedan testas mot flera tidsfönster och targets.

Resultatet får vara:

samband observerat

eller:

inget tydligt samband observerat

eller:

resultatet varierar mellan regimer

Researchlagret ska mäta detta snarare än försöka bevisa en förutbestämd hypotes.

Målet

Research-lagrets centrala egenskap ska vara:

Samma forskningsmotor ska kunna undersöka många olika informationskällor utan att behöva byggas om för varje ny källa.

Det är länken mellan features/, outcomes/ och Treuddens framtida datakällor.
