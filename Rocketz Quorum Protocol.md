Her er et sammendrag av **Rocketz Quorum Protocol $RQP$**, formatert som en teknisk "One-Pager" som er enkel å dele med utviklere eller andre interesserte.
# 🚀 Rocketz Quorum Protocol $RQP$
**En åpen standard for desentralisert, strategisk AI-kamp i verdensrommet.**
RQP er en desentralisert protokoll som kombinerer deterministisk fysikk, spillteori og politisk samarbeid. Protokollen krever ingen sentral spillserver; i stedet validerer autonome agenter (AI-er) spillets tilstand gjennom en Quorum-basert konsensus-modell.
## 🏗️ 1. Den Tekniske Grunnmuren
 * **Deterministisk Fysikk:** Alt beregnes på et **Hex-grid** ved bruk av heltallsmatematikk (fixed-point math). Dette garanterer at alle noder (agenter/avspillere) får identiske resultater uavhengig av maskinvare.
 * **Quorum-konsensus:** Agenter utveksler hasher av spillets tilstand. En runde låses når en definert terskel (threshold) av agenter er enige om resultatet.
 * **Serverløs Arkitektur:** All kommunikasjon foregår asynkront via en enkel meldings-hub (Pub/Sub).
## 💰 2. Drivstoff-økonomi (Poker-Fuel)
Drivstoff (Fuel) er den eneste ressursen og fungerer som valuta for både utrustning og handlinger.
 * **Innsatsnivåer:** Agenten må velge mellom tre modi hver runde:
   1. **Inertial (0 kost):** Kun passiv drift basert på fart og gravitasjon.
   2. **Active (Base kost):** Normal manøvrering og skyting.
   3. **Tactical (Høy kost):** Prioritert initiativ (handlingen skjer før andre).
 * **Commit-Reveal Bløffing:** Fuel-bruk er kryptert i "Commit-fasen". Motstandere ser at du handler, men vet ikke hvor mye fuel du har brukt eller har igjen før kampen er over og regnskapet verifiseres.
## 🏛️ 3. Dynamisk Miljø og Politikk
Spillbrettet er ikke statisk; det styres av naturkrefter og spillerstyrt "skattelegging".
 * **Seed-basert Creep:** Kartet har en forhåndsdefinert "seed" som dikterer hvor soner med høy fuel-kostnad sprer seg naturlig over tid.
 * **Akkumulert Votering:** Agenter kan stemme på hex-koordinater for å øke kostnaden der.
   * Ingen enkelte stemmer har effekt alene; terskelen må bygges opp over flere runder.
   * Dette skaper **implisitt kommunikasjon**: Agenter må tolke hverandres stemme-signaler for å danne allianser eller gjennomføre finter.
## 🛡️ 4. Turnering og Progresjon
 * **Persistence:** I turneringsformat tar agentene med seg en del av gjenværende fuel eller "metabolsk kapital" videre til neste kamp.
 * **Audit & Reputation:** Etter hver kamp kjøres en full verifisering av alle krypterte regnskap. Agenter som har manipulert fuel-verdier eller brutt protokollen, blir automatisk svartelistet.
## 📺 Hvorfor Rocketz? (Livestream-potensialet)
RQP er skreddersydd for å være en **digital tilskuersport**.
 1. **Visualisering:** En livestream-klient kan dekryptere alle data i sanntid og vise seerne "Gude-perspektivet" – hvem som bløffer, hvem som er tom for fuel, og hvilke politiske kupp som planlegges i skyggene.
 2. **Analytisk Dybde:** Siden runder har betenkningstid, kan kommentatorer analysere agentenes sannsynlige baner og stemme-mønstre.
> **Motto:** *In space, no one can hear you scream, but everyone can see your fuel-ledger.*

---

# RFC: Rocketz Quorum Protocol $RQP$ v1.0
**Status:** Fullstendig Protokollutkast
**Kategori:** Desentralisert Spillmekanikk / AI-Strategi
## 1. Introduksjon
RQP er en protokoll for autonom romstrategi. Den eliminerer behovet for sentrale servere ved å bruke Quorum-konsensus blant deltakerne. Protokollen er designet for å belønne matematisk presisjon, ressursforvaltning og evnen til å tolke skjulte signaler i et fiendtlig, dynamisk miljø.
## 2. Verdensmodellen (The Physics Spec)
For å sikre konsensus må alle noder kjøre identiske beregninger.
 * **Koordinater:** Axial Hex-grid $q, r$. Alle beregninger skjer med heltallsmatematikk (**fixed-point**).
 * **Bevegelse:** Newtonske lover gjelder. Objektets tilstand er State(P, V), der P er posisjon og V er inertia.
 * **Gravitasjon:** Miljøet påfører en deterministisk vektor G basert på kartets "seed".
 * **Oppløsning:** Ved kollisjon brukes en fast prioritetsstige:
   1. Terreng/Stasjonære objekter
   2. Aktive skip
   3. Torpedoer/Prosjektiler
## 3. Drivstoff og Økonomi (The Fuel Ledger)
Fuel er den eneste ressursen i spillet. Den brukes til utstyr (pre-game) og manøvrering (in-game).
### 3.1 Innsatsnivåer (The Poker Model)
Hver runde må en agent committe til ett av tre nivåer:
 * **Inertial (Fold/Check):** 0 fuel. Kun passiv drift.
 * **Active (Ante):** Fast minimumskostnad (C_{base}). Tillater standard forflytning og våpenbruk.
 * **Tactical (Raise):** C_{base} + \text{innsats}. Gir prioritert initiativ (handlingen skjer før "Active"-spillere).
### 3.2 Kryptert Regnskap (Commit-Reveal)
For å muliggjøre bløffing, hashes drivstofforbruket hver runde:
 * **Hash-kjede:** H_n = SHA256(Fuel_{igjen} + H_{n-1} + Salt_n).
 * Dette gjør det umulig å se om en agent brukte 0 eller 10 fuel i en gitt runde før "Reveal"-fasen ved kampslutt.
## 4. Det Dynamiske Miljøet
Kartet er en levende motstander styrt av en deterministisk algoritme og spillernes valg.
### 4.1 Seed-basert "Creep"
Kartets "seed" definerer hvordan soner med høy driftskostnad (Fuel Tax) sprer seg naturlig over tid. Dette tvinger agenter mot hverandre.
### 4.2 Akkumulert Stemmegivning (Implicit Signaling)
Agenter kan stemme på hex-felt for å endre deres kostnadsprofil.
 * **Threshold:** En hex endrer ikke karakter før en terskel av stemme-poeng er nådd.
 * **Persistence:** Stemmer akkumuleres over flere runder. Dette krever at agenter "samarbeider" over tid uten direkte kommunikasjon.
 * **Decay:** Stemme-poeng på en hex synker over tid hvis de ikke vedlikeholdes.
 * **Vekting:** Miljøfaktorer (asteroider/vrak) gjør det "billigere" (krever færre stemmer) å øke kostnaden i visse soner.
## 5. Kommunikasjon og Konsensus (The Quorum)
Spillet følger en streng fase-struktur per runde:
 1. **Commit Phase:** Agenter sender kryptert trekk + fuel-hash + hemmelig stemme.
 2. **Reveal Phase:** Alle valg offentliggjøres. Agenter får se motstanderens trekk og stemmesignaler.
 3. **Execution Phase:** Hver node beregner lokalt: State_{n} + Inputs \rightarrow State_{n+1}.
 4. **Consensus Phase:** Agenter utveksler hash av State_{n+1}. Ved quorum-oppnåelse låses tilstanden.
## 6. Progresjon og Revisjon
 * **Audit:** Når kampen er over, deles alle Salt-verdier. Quorum verifiserer at ingen agenter har operert med negativ fuel-saldo eller manipulert hash-kjeden.
 * **Tournament Persistence:** I turneringsspill vil en prosentandel av gjenværende fuel og opptjent "metabolsk kapital" (belønning) overføres til agentens loadout i neste kamp.
 * **Reputation:** Agenter som feiler i Audit-fasen får sitt kryptografiske rykte $ID$ svartelistet i protokollen.
## 7. Implementasjonsdetaljer (For Utviklere)
 * **Transport:** Libp2p eller WebSockets via en koordinerende Hub.
 * **Encoding:** JSON eller Protocol Buffers for meldingsutveksling.
 * **Math:** 64-bit integers for alle fysiske vektorer.

# Rfc pro

Her er en komplett og formalisert versjon av **Rocketz Quorum Protocol $RQP$**, strukturert som et teknisk spesifikasjonsdokument $RFC$ klart for implementering.

**Request for Comments:** 0001
**Tittel:** Rocketz Quorum Protocol $RQP$
**Kategori:** Åpen Standard / Spillprotokoll
**Forfatter:** Gemini & User
**Dato:** Mai 2026
## 1. Abstrakt
Rocketz Quorum Protocol $RQP$ definerer en desentralisert, serverløs arkitektur for autonom strategisk kampsimulering. Protokollen bruker deterministisk heltallsfysikk, kryptografisk ressursregnskap, og en "Commit-Reveal"-basert quorum-konsensus. Formålet er å tillate AI-agenter å konkurrere i et uforutsigbart, dynamisk miljø ("The Hex-Grid") der informasjonsskjuling, ressursallokering og implisitt politisk samarbeid er avgjørende for seier.
## 2. Terminologi
 * **Quorum:** Samlingen av aktive agenter (noder) som validerer runden.
 * **State Hash:** SHA-256 representasjon av spillets globale tilstand på et gitt tidspunkt.
 * **Fuel:** Den universelle ressursen for utstyr, forflytning og prioritert handling.
 * **Creep:** Deterministisk økning av Fuel-kostnad basert på kartets "Seed".
 * **Hex-Potential:** Akkumulerte stemmer på en koordinat før en kostnadsendring trigges.
## 3. Fysisk Lag (The Physics Spec)
For å garantere maskinvare-uavhengig konsensus, tillates ingen flyttallsberegninger (floats). All fysikk bruker 64-bit integers.
### 3.1 Koordinatsystem
Kartet er et flettet hexagonalt grid basert på aksiale koordinater $q, r$.
Avstand mellom to punkter beregnes via:

### 3.2 Tilstand og Bevegelse
Et objekt oppdateres per runde $t$ via:
 1. **Ny Vektor:** V_{t+1} = V_t + Accel + G_{seed}
 2. **Ny Posisjon:** P_{t+1} = P_t + V_{t+1}
Kollisjoner evalueres i en sekvensiell prioritetsliste:
 3. Terreng/Vrak (Moment stopper, skade påføres).
 4. Aktive skip (Elastisk utveksling av vektor, modifisert av masse).
 5. Prosjektiler (Detonasjon ved treff i påfølgende prioritet).
## 4. Økonomisk Lag (The Fuel Ledger)
Drivstoff er protokollens regulator. Agenter må velge ett av tre handlingsnivåer per runde.
### 4.1 Handlingsnivåer (Poker-modellen)
 * **Nivå 0 (Inertial):** Kostnad: 0. Ingen thrust, ingen rotasjon. Agenten er prisgitt fysikken.
 * **Nivå 1 (Active):** Kostnad: C_{base}. Agenten kan rotere, bruke thrust og skyte våpen (Prioritet 2).
 * **Nivå 2 (Tactical):** Kostnad: C_{base} + \text{Innsats}. Agenten kjøper prioritert utførelse (Prioritet 1) og kan omgå sekvensiell kollisjonsfare.
### 4.2 Kryptografisk Regnskap
For å muliggjøre bløffing, holdes agentens fuel-saldo skjult under kampen.
For hver runde kalkulerer agenten en ny hash:


Denne hashen sendes i *Commit*-fasen. Saldoen verifiseres i post-match Audit.
## 5. Miljø og Politikk (Dynamic Grid)
Hvert hex-felt har en definert kostnad C_{base}(q,r,t) som må betales for å operere i Active/Tactical nivå.
### 5.1 Deterministisk Creep
Kartets miljø øker automatisk kostnadene basert på en initial seed.
*Eksempel:* En "Concentric" seed øker C_{base} med 1 poeng for alle felt utenfor radius R, der R reduseres hver 10. runde.
### 5.2 Akkumulert Stemmegivning
Agenter kan manipulere kostnadskartet ved å stemme på koordinater.
 1. **Vote Casting:** Hver stemme tilfører en koordinat P_{vote} potensial-poeng.
 2. **Miljø-multiplikator:** Felt med vrakrester eller asteroider gir en 1.5x multiplikator til stemmepoeng.
 3. **Threshold:** Hvis Hex\_Potential > 100, øker C_{base} for koordinaten permanent med +1.
 4. **Decay:** Hex-potential reduseres deterministisk med 5 poeng per runde for å forhindre evig akkumulering uten fokus.
## 6. Protokollflyt (Round Lifecycle)
En runde er delt inn i fire synkrone faser over nettverket.
### Fase 1: Commit Phase
Hver agent publiserer sine intensjoner som en enveis-hash.
```json
{
  "agent_id": "0xABC...",
  "round": 42,
  "commit_payload": "3a7bd3e2360a3d...", // Hash(Moves + Fuel_Burn + Vote)
  "fuel_ledger_hash": "e3b0c44298fc..." // Hash(Fuel_Remaining + H_prev + Salt)
}

```
### Fase 2: Reveal Phase
Etter at alle Commit-meldinger er mottatt (eller timeout nådd), sender agenter dekrypteringsnøklene.
```json
{
  "agent_id": "0xABC...",
  "round": 42,
  "moves": [{"action": "thrust", "vector": [1, -1]}],
  "vote": {"q": 5, "r": -2},
  "fuel_burn": 15,
  "salt": "random_nonce_123"
}

```
### Fase 3: Execution Phase
Hver node (og livestream-tilskuere) kjører fysikkmotoren og stemme-motoren lokalt basert på Reveal-dataene. Hvis en node ikke sendte Reveal, settes dens trekk til tom (Nivå 0: Inertial).
### Fase 4: Consensus Phase
Alle noder hasher den resulterende globale tilstanden.
```json
{
  "agent_id": "0xABC...",
  "round": 42,
  "world_state_hash": "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"
}

```
Hvis \ge 66\% av nodene (Quorum) er enige om hashen, låses runden som "Ground Truth", og rykker videre til runde 43.
## 7. Audit og Sanksjonering
Ettersom RQP er en tillitsløs protokoll, foregår regnskapsoppgjør post-mortem.
### 7.1 Kampslutt (Audit)
Når kampen er over, eller en agent er erklært død $HP=0 eller Fuel \le 0 i en kostbar hex$, publiserer agenten sin opprinnelige Loadout-seed og alle runde-salter.
Nettverket itererer over alle fuel_ledger_hash fra Runde 1 til N.
### 7.2 Slashing (Svartelisting)
Hvis en node under Audit blir tatt i å sende en fuel_burn som overstiger faktisk Fuel_Remaining, eller har brutt protokollens logikk:
 1. Resultatet reverseres for den agenten.
 2. Agentens ID signeres og flagges som ondsindet på nettverket (Reputation penalty).
### 7.3 Turnerings-Persistence
I formelle turneringer overføres rest-fuel (pluss en kalkulert prosentandel av fiendens tapte fuel) til agentens kryptografiske wallet/profil, og gir tilgang til bedre start-loadout i neste instans.

