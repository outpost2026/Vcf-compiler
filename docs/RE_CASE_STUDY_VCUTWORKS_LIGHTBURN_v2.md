# Reverse Engineering Case Study: Ruida VCF & LightBurn DXF

**Verze:** 2.0  
**Datum:** 12. 6. 2026  
**Status:** Revidováno dle developera — empirická data, bez subjektivního hodnocení


## 1. Executive Summary

Tento dokument je kronikou reverzního inženýrství dvou proprietárních CAM formátů: **.VCF** (Ruida/VCutWorks) a **.DXF exportovaného z LightBurn**. Popisuje *co* bylo objeveno, *proč* to bylo nutné, a *jak* k tomu došlo — metodiku, problémy, nástroje a výsledky. Dokument je psán jako otevřená kazuistika pro komunitu uživatelů CNC, laserů a CAM softwaru.

### Empirická fakta

| Metrika | Hodnota |
| - | - |
| Celková doba projektu | 14. 5. – 11. 6. 2026 (29 dní) |
| Verzí parseru | V1 → V22 |
| Testovacích VCF souborů | 12+ |
| Testovacích DXF souborů | 7 |
| Golden master testů | 10 testů (4 smoke + 4 golden master + 2 determinism) |
| Branchí | 7 feature branches |
| Commitů (DXF) | 20 (od v2.2.0 baseline, ~2,5/den) |
| Mergů do main | 0 (vše ve feature branches) |
| Merge konflikty | 0 |
| Tagy | 1 (v2.2.0) |
| Pull requesty | 0 |
| Push na remote | Ano, všechny branche |
| Použitých LLM modelů | 5 (DeepSeek V4, Gemini, Claude, Groq, marginálně ChatGPT) |
| LLM operace | Primárně OpenCode CLI agentní nástroj s API (DeepSeek + Gemini), chat UI pro rychlé iterace |



## 2. Co, Proč a Jak

### Co bylo cílem?

Firma vyrábějící akustické panely potřebovala **automatizovat extrakci CNC dat pro ERP účely**. Binární .VCF soubory (generované VCutWorks) obsahují kompletní technologické parametry po zpracování CNC technologem — rychlosti, typy nástrojů, hloubky řezu, délky drah. Bez schopnosti tyto soubory číst nelze data hromadně zpracovat.

Paralelně existují **.DXF soubory exportované z LightBurn**, které slouží jako vstup od grafiků. Jsou to pre-process výkresy — geometrie bez kontextuálních CNC dat. Tyto DXF soubory teprve CNC technolog importuje, nastaví parametry a exportuje jako hotové VCF pro plotr.

Logika výzkumu byla:

1. **Přesné parsování VCF souborů** — již obsahují kontext CNC technologa (technologické postupy, parametry vrstev, rychlosti, nástroje)

2. **Hromadné zpracování** — ML, statistické metody, korelace geometrie DXF → parametry VCF

3. **Generalizace práce CNC technologa** — schopnost s vysokou spolehlivostí odhadnout parametry výsledného VCF pouze z geometrie DXF výkresu

Tím by bylo možné již ve fázi grafického návrhu (DXF) odhadnout budoucí charakteristiky výrobního procesu — zejména čas zpracování, náklady a další implikace pro firmu i zákazníky.

### Proč to bylo nutné?

1. **Žádná veřejná dokumentace .VCF neexistuje.** Formát je proprietární, bez SDK, bez API, bez specifikace.

2. **LightBurn DXF se liší od standardního DXF.** Standardní knihovny (např. ezdxf) předpokládají AutoCAD ACI mapování barev, které LightBurn nedodržuje.

3. **Tacitní znalosti operátora nejsou formalizované.** Know-how kalibrace, seřizování a odhadu časů je vázáno na jednu osobu.

4. **Nikdo kromě CNC operátora nemá přehled o délce procesu.** Automatizace, byť částečná, by mohla být firmě prospěšná.

### Jak se k tomu přistoupilo?

Autor zvolil iterativní reverzní inženýrství s více nezávislými validačními metodami. Všechny fáze (0–6) proběhly **výhradně v období spolupráce autora s firmou** (14. 5. – 11. 6. 2026):

1. **Tacitní sběr:** Stínování hlavního technologa, ruční deníky, digitalizace know-how

2. **Synthetic Ground Truth:** Vytvoření testovacích VCF/DXF s přesně známou geometrií v trial verzích

3. **Diferenciální analýza:** Pair diff párů souborů lišících se v 1 elementu

4. **Fyzikální validace:** Odečítání reálných časů z displeje CNC plotru, porovnání s Preview simulací VCutWorks

5. **Ground Truth:** Export VCF→DXF, měření v LightBurn, porovnání s parserem

6. **Testování:** Golden master regression, determinism tests


## 3. Metodika Autora

### 3.1 Diferenciální analýza binárních párů (Pair Diff)

Vytvořeny dva téměř identické VCF soubory lišící se přesně v jednom elementu (např. 1 obdélník vs. 2 obdélníky). Binárním rozdílem (hex diff) odhalena struktura formátu — kde začíná geometrie, velikost elementu, velikost segmentu.

### 3.2 Fyzická validace — Preview vs. Skutečnost

VCutWorks obsahuje funkci **Preview** (v záložce EDIT), která simuluje řezný proces plotru. Autor zjistil, že predikce Preview se **výrazně liší od skutečného času obrábění** na CNC plotru. Hodnoty byly ručně odečítány z displeje CNC (který po dokončení každého procesu zobrazuje celkovou dobu) a porovnávány se simulací. Tato diskrepance vedla k detailnějšímu výzkumu vztahu mezi geometrií, rychlostí a výsledným časem.

### 3.3 Transfer Learning z CNC Waterjet

Zkušenosti z předchozího projektu (CNC vodní paprsek) adaptovány na oscilační nůž — fyzikální model kinematiky stroje, corner slowdown, plunge overhead.

### 3.4 Clean Room Testování

Vytvořeny syntetické testovací soubory v trial VCutWorks s přesně známou geometrií: obdélník (2790×1200 mm, obvod 7980 mm), kružnice (r=500 mm), kombinace polygonů + kružnic + polylines. Každý soubor validován v LightBurn před použitím jako ground truth.

### 3.5 Golden Master Regression Testing

Po stabilizaci parseru uložena baseline JSON výstupů. Každá změna kódu porovnána s baseline — odchylka (kromě timestamp) detekována jako regrese. Tento přístup odhalil regresi kružnic.

### 3.6 SNR Analýza (Data Trimming)

Klasifikováno 27+ výpočetních modulů dle prediktivní hodnoty pro cutting time do Tier 1–5. Zjištění: **25 % kódu řídí \>85 % variance**. Tato analýza umožnila prioritizovat vývoj na moduly s nejvyšším přínosem.

### 3.7 Epistemický Rámec

Každá heuristická hodnota v parseru má explicitní `validation\_status`:

- **empirical** — validováno na produkčních datech

- **calibrated** — validováno v laboratorních podmínkách

- **hypothesis** — spekulativní, čeká na validaci


## 4. Časová Osa Projektu

**Všechny fáze proběhly v období 14. 5. – 11. 6. 2026, výhradně během spolupráce autora s firmou.**

### Fáze 0 – Tacitní Sběr

Autor stínoval hlavního technologa (operátora s dvacetiletou praxí). Ručně si zapisoval: kalibraci nuly, oscilační frekvenci, barevnou nomenklaturu vrstev, nesting pravidla, fixační techniky. Deníky byly digitalizovány a staly se základem pro technologická pravidla parseru.

### Fáze 1 – Synthetic Ground Truth

Staženy trial verze VCutWorks a LightBurn. Vytvořeny testovací VCF/DXF soubory s přesně známou geometrií pro validaci.

### Fáze 2 – Hex Analysis

Hex dump. Hledání patternů. Identifikace IEEE 754 double floatů (little-endian). Objev kódování Windows-1250 pro textová metadata. Zjištění: formát je deterministická serializace, není šifrovaný ani komprimovaný.

### Fáze 3 – V1 až V9: První Parser

- **V1–V3:** Extrakce metadat (DXF cesta, fonty, tagy)

- **V4–V6:** Fuzzy matching VCF↔DXF, instruction\_count jako proxy složitosti, MD5 deduplikace

- **V7–V9:** Extrakce technologických parametrů vrstev (rychlost, nástroj, H1/H2, V-slot). 100% shoda s GUI.

### Fáze 4 – V10 až V16: Od Fatální Chyby ke Stabilizaci

- **V10 — Fatální chyba:** Parser četl padding float 1.0 jako délku → kruh r=500 mm → 8 mm (místo 3141 mm). Ground truth validace odhalila diskrepanci.

- **V11 — Rekonstrukce geometrie:** Úplné opuštění pevného offsetu. Identifikace 74B segmentových bloků. Výpočet délky jako součtu euklidovských vzdáleností.

- **V12 — Edge Completion:** Uzavírání kontur, off-by-byte fix.

- **V13 — CAM Grouping:** Pokus o podporu sloučených geometrií — selhání, desynchronizace, 0 elementů.

- **V14 — Barevné mapování:** Objev color-to-layer mapping. Regrese kružnic (poloměr nadhodnocen o 41 %).

- **V15 — Stabilizace:** Oprava kružnic (2πR). Maskování cutter\_type\_id.

- **V16 — Univerzální parser:** Jednotná segmentová smyčka pro všechny typy. Přesnost 99,99 %.

### Fáze 5 – DXF Parser

Paralelní vývoj DXF indexeru odhalil **odchylku LightBurn od standardního ACI mapování** — LightBurn používá vlastní 32barevnou CAM paletu. Implementována **euklidovská RGB interpolace** (hledání nejbližší barvy minimalizací (ΔR)²+(ΔG)²+(ΔB)²). Další objevy: INSERT bloky, SPLINE handler, ACI priority pro tool assignment.

### Fáze 6 – V20 až V22: Cloud Deployment a Vizualizace

Parser migrován na GCP Cloud Run (serverless, Docker → Python 3.11). Streamlit dashboard. Dvě kritické opravy: kružnice posunuté o poloměr v PNG a chybějící vrstvy (barvení dle typu elementu místo vrstvy, \[:600\] limit).


## 5. Problémy a Jejich Řešení

### 5.1 Preview vs. Realita (V7–V9)

**Problém:** Simulace Preview ve VCutWorks se výrazně lišila od reálného času na CNC plotru.

**Metoda:** Autor manuálně odečítal hodnoty z displeje CNC po dokončení každého procesu a porovnával je s Preview simulací.

### 5.2 Falešná délka z pevného offsetu (V10)

**Problém:** Parser interpretoval padding float 1.0 jako délku. Kruh r=500 mm → 8 mm.

**Řešení:** Úplné opuštění pevného offsetu. Parser nyní rekonstruuje délku ze souřadnic bodů — součet euklidovských vzdáleností.

### 5.3 Regrese kružnic (V14)

**Problém:** Při refaktoringu barevného mapování došlo k chybě — poloměr 500 mm → ~707 mm (+41 %).

**Root cause:** Refactoring bez unit testů. Kružnice uložena jako 4 kvadrantové oblouky — parser četl Y-ové souřadnice z nesouvisejících dat.

**Řešení:** Výpočet pouze z X-ových souřadnic.

### 5.4 Desynchronizace (V13)

**Problém:** Do-while smyčka pro Grouping způsobila čtení paddingových dat jako falešných elementů. Pro jeden soubor: 0 elementů (fatální selhání).

**Řešení:** Přepracování na segmentové čtení s pt\_count.

### 5.5 LightBurn ACI Divergence

**Problém:** LightBurn při exportu DXF nepoužívá standardní AutoCAD ACI→RGB mapování. Např. ACI 4 (standardně cyan) je v LightBurn mapován jinak.

**Řešení:** Sestavení kompletní 32barevné LightBurn CAM palety a euklidovská RGB interpolace.

### 5.6 INSERT Bloky

**Problém:** Až 50 % geometrie neparsováno — LightBurn používá INSERT entity (reference na bloky).

**Řešení:** Implementace block explosion: extrakce definice bloku, kopírování entit, aplikace transformační matice.

### 5.7 Tool Assignment Conflict

**Problém:** Dvě nezávislé logiky přiřazení nástroje (ACI color mapping vs. geometrická heuristika) si odporovaly.

**Řešení:** ACI mapping má vyšší prioritu. Při konfliktu: `tool\_conflict\_detected = True` + seznam konfliktních entit.

### 5.8 PNG Vizualizace Bugy (V21–V22)

- **Kružnice posunuté:** Střed brán jako startovní bod oblouku, ne geometrický střed

- **Chybějící vrstvy:** Barvení dle typu elementu ignorovalo vrstvu + \[:600\] limit


## 6. Role LLM v Procesu

### 6.1 Modely a Nástroje

Autor použil **všechny dostupné LLM modely**: Anthropic (Claude), Gemini, DeepSeek, Groq, marginálně ChatGPT.

**Primárním nástrojem integrace LLM** byl agentní nástroj OpenCode CLI s API Gemini a API DeepSeek. Autor si pro tyto účely zaplatil komerční tier (Google Plus + DeepSeek API, v rozsahu desítek USD). Tento rozsah výzkumu není dle autora realizovatelný ve standardním webovém UI — je nutné provádět hloubkový a paralelní výzkum přes API.

**Webové chat UI** bylo využíváno pro:

- Rychlé iterační dotazy

- Cross-validaci mezi modely

- Sémantický trimming textů

- Tvorbu jednoduchých Python skriptů

- Inspiraci — jako encyklopedie a ontologická báze

**Samotná vývojová činnost** probíhala s agentními API v OpenCode CLI, se zapojením lokálního vývojového prostředí autora a všech artefaktů vytvořených během výzkumu.

### 6.2 Cross-Validace

Rozdíly mezi modely odhalovaly chyby v RE interpretaci. Pokud dva modely vrátily odlišnou interpretaci, autor věděl, že je třeba další analýza.

### 6.3 Handoff Formát

Autor vyvinul strojově čitelný handoff formát (JSON) pro předávání kontextu mezi iteracemi. Každý handoff obsahuje project\_context, version\_history, test\_suite, known\_issues, lessons\_learned. Celkem vzniklo 15+ handoff dokumentů.

### 6.4 10 Golden Rules

Formalizovaná pravidla pro spolupráci s LLM:

1. Determinismus — stejný vstup = stejný výstup

2. Config \> Code — parametry do JSON, nikdy hardcoded

3. Test-First — před implementací test, který selže

4. Epistemic Transparency — každá hodnota má validation\_status

5. Logging \> Print — strukturovaný logging

6. Type Hints — plné typové anotace

7. Version Stamping — každý modul má verzi

8. No Magic Numbers — konstanty s pojmenováním a zdůvodněním

9. Blacklist — zakázané patterny (eval, random, time.sleep, pevné cesty)

10. Handoff Before Break — před pauzou vygenerovat handoff JSON


## 7. Co Vzniklo

### 7.1 VCF Parser

Parser proprietárního binárního formátu, psaný v Python 3.11 (pouze struct + math, bez externích knihoven), který extrahuje metadata, technologické parametry vrstev, přesnou délku dráhy (\>99,98 % přesnost), mapuje elementy do vrstev, predikuje rizika a generuje 2D PNG vizualizaci.

### 7.2 DXF Indexer

Parser DXF souborů exportovaných z LightBurn s euklidovskou barevnou interpolací do LightBurn CAM palety, block explosion, SPLINE handler, RDP zjednodušením křivek a prostorovou analýzou.

### 7.3 Streamlit Dashboard

Cloudová aplikace na GCP Cloud Run s HUD+MFD architekturou, predikcí času ±2–5 %, knowledge base enginem a downloadem JSON/MD/CSV/PNG/TXT.

### 7.4 ERP Integrace

Google Apps Scripty → Google Sheets pipeline a Flask REST API pro ERP.

### 7.5 Znalostní Báze

15+ dokumentů pokrývajících specifikaci formátu, dev history, layer parameters, compiler knowledge base, DXF CAM encoding, metodologii, epistemický rámec a tuto kazuistiku.


## 8. Deployment

| Parametr | Hodnota |
| - | - |
| Platforma | GCP Cloud Run |
| Region | europe-west1 |
| Kontejner | Docker → python:3.11-slim |
| RAM | 512 MiB |
| Timeout | 900 s |
| Cold start | ~5–60 s (min-instances=0) |
| Min/Max instances | 0 / 1 |



## 9. Cross-validace a Testování

### 9.1 VCF Testovací Sada

12+ souborů — jednoduché tvary, kružnice, polylines, reálné motivy (botanic), agregované zakázky.

### 9.2 DXF Testovací Sada

7 souborů — PCB (A, C), slotové panely, INSERT bloky, SPLINE, jednoduché tvary.

### 9.3 Výsledky

| Metoda | Výsledek |
| - | - |
| Golden master testy | 10/10 PASS |
| Determinism testy | 2/2 PASS |
| LightBurn measure | \>99,98 % přesnost (odchylka \<0,02 %) |
| GUI screenshot | 100% shoda rychlostí |
| Synthetic clean room | Ověřeno na základní sadě |
| Pair diff (hex) | Odhalení struktury formátu |



## 10. Závěrečné Zhodnocení

### 10.1 Vhodnost Publikace

Dokument je publikován jako **otevřená kazuistika metodologie RE**, nikoli jako technická specifikace formátu. Obsahuje empirická data doložitelná z git historie (20 commitů, 7 branchí, 0 merge konfliktů), validační výsledky (10/10 testů PASS) a chronologii vývoje.

Neobsahuje proprietární detaily formátů (offsety, signatury, bitové masky).

### 10.2 Empirická Data z Developer Reportu

| Metrika | Hodnota |
| - | - |
| Branchí vytvořených | 7 (vše feature/) |
| Commitů (DXF repo) | 20 |
| Frekvence commitů | ~2,5/den po dobu 8 dní |
| Mergů do main | 0 |
| Push na remote | Ano |
| Tagy | 1 (v2.2.0) |
| Merge konflikty | 0 |
| Pull requesty | 0 |
| Metodologické dokumenty | 5+ |
| LLM modelů | 2 v té době (DeepSeek V4 + Gemini Flash 3.5) |
| Detekovaná porušení blacklistu | 3× (hardcoded stock rectangle) |


### 10.3 Poučení pro Komunitu

1. **LightBurn DXF ≠ AutoCAD DXF.** Standardní DXF knihovny selhávají na LightBurn exportech kvůli proprietární barevné paletě. Řešením je euklidovská RGB interpolace do referenční palety.

2. **INSERT bloky nejsou geometrie.** Bez block explosion ztratíte ~50 % geometrie.

3. **Golden master testy nejsou akademismus.** Odhalily regresi kružnic, která by se projevila až při výrobě.

4. **LLM vyžaduje guardrails.** 10 Golden Rules, cross-validace mezi modely, handoff dokumentace.

5. **RE binárního formátu vyžaduje metodiku.** Pair diff, clean room testy, fyzikální validace, ground truth — adhoc přístup selhává.


*Dokument publikován jako otevřená kazuistika reverzního inženýrství. Obsahuje empirická data, metodologii a ponaučení — nikoli proprietární detaily formátů.*

