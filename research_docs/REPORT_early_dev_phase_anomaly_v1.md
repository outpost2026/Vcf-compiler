# REport: Early Development Phase Analysis — The "First Working" Anomaly

**Datum:** 2026-06-29  
**Účel:** Identifikovat vývojovou fázi, kdy první syntetický VCF úspěšně načetl VCutWorks, analyzovat co bylo jinak a co se následně změnilo.

---

## 1. METODIKA

Git historie byla analyzována chronologicky od prvního commitu (`171e2e7`) po současnost (`HEAD`). Každý commit byl zkoumán z hlediska změn v `_writer.py` a `_reader.py`. Binární výstupy byly extrahovány pomocí `git show` a analyzovány strukturně.

---

## 2. NALEZENÁ FÁZE — COMMIT `4ba9446`

**Hash:** `4ba9446998e92affc9618fa1271edbb81b886e9d`  
**Datum:** Sat Jun 27 12:53:50 2026  
**Message:** "feat: fix VCF writer header format (0x13 prefix, 257 blocks, stock dims, no trailer) + dxf adapter + ACI mapping config"

### 2.1 Co tento commit uměl

- Vygeneroval `circle_from_dxf.VCF` z `circle_500_single_aci.dxf`
- VCutWorks načetl tento VCF a **zobrazil geometrii** (kruh)
- ACI vrstvy/barvy nebyly korektní (řezné parametry)

### 2.2 Writer — klíčové vlastnosti (tehdy)

```python
# Layout bloků: ACTIVE FIRST, pak empty
for layer in self._layers:
    data += self.encode_layer_block(layer, LAYER_BLOCK_SIZE)

empty_count = TOTAL_LAYER_BLOCKS - len(self._layers)
if empty_count > 0:
    data += b'\x00' * (LAYER_BLOCK_SIZE * empty_count)
```

**Pole layer bloku:**

| Offset | Pole | Hodnota (příklad) |
|--------|------|-------------------|
| 0 | output_flag | 1 (uint32) |
| 4 | speed | 200.0 (float64) |
| **12** | **color** | **0x00FFFFFF = BGR(255,255,255)** (uint32) |
| 32 | cutter_idx | 0 = Vibrate cutter (int32) |
| 76 | **H1** | 2.0 (float64) |
| 84 | feed | 1 (int32) |
| 92 | **H2** | -0.3 (float64) |
| 602-609 | linked-list | **všechny nuly** (nepoužito) |

**Hlavička:**
- Bez MACHINE_PROFILE (jen preamble = 53 bytů)
- POST_STOCK_HEADER: `0x00000000` + double 100.0 + uint16 1 = 14 bytů

**Geometrie:**
- Bez GEOMETRY_HEADER_TEMPLATE (bytes 12-44 = nuly)
- pt_count = 1 (1 segment pro kruh — ne 4)
- Bez is_closed epsilon

**Trailer:**
- `write()` volá pouze `fd.write(h + b)` — trailer se NEZAPISUJE
- trailer() metoda vrací `b'\xd7'` ale není volána

---

## 3. CO SE STALO PAK — KRONOLOGIE ZMĚN

### Commit `5ce3e80` — Blok order swap
```
Změna: pořadí bloků aktivní/prázdné → PROHOZENO
```
- **Writer:** prázdné bloky FIRST, aktivní bloky LAST
- **Reader:** forward scan z block 0 (místo backward skenu z geometrie)
- Všechny field offsety stejné jako v `4ba9446`

### Commit `a19084b` — feed_count = 0, is_closed
```
Změna: feed_count default 1→0, přidáno is_closed (geom_type=1)
```

### Commit `4ead359` — REVERT feed_count
```
Návrat: feed_count default 0→1
```

### Commit `ed867c1` — ⚠️ KRITICKÁ ZMĚNA — COLOR PŘESUNUT
```
Změny:
1. COLOR z offsetu 12 → offset 76
2. H1 z 76 → 80
3. feed z 84 → 88
4. H2 z 92 → 96
5. V-slot fields posunuty o +4
6. **Linked-list mechanismus přidán** (posledních 8 B bloků)
7. Default H1 v write() změněn z 2.0 na 10.0
```

### Commit `a1b339c` — GEOMETRY_HEADER_TEMPLATE + circle 4 segments
```
Změny:
1. GEOMETRY_HEADER_TEMPLATE přidán do bytes 12-44 geometrie
2. is_closed epsilon 0.001
3. Circle element → 4 segmenty (pt_count=4)
4. _path_types mechanismus
```

### Commit `ea8aa2b` — MACHINE_PROFILE + trailer
```
Změny:
1. MACHINE_PROFILE (418 B) do hlavičky
2. TRAILER_PREFIX (199 B) + DXF cesta
3. write() nyní volá h + b + t (trailer přidán)
4. EMPTY_BLOCK_COUNT=256 (Total=256+active)
5. Block index counter at [10]
6. color at [76] vynucen na 0 (vždy černá)
```

---

## 4. KLÍČOVÉ NÁLEZY

### Nález A: Náš reader NIKDY nefungoval s výstupem writeru z `4ba9446`

```python
# Test: reader (backward scan, k=1..32) na circle_from_dxf.VCF
# Výsledek: Found 0 layers
```

Reader v `4ba9446` používal backward scan s max k=32. Ale aktivní blok byl na pozici k=257 (poslední blok před geometrií), což backward scan nenašel. **VCutWorks MUSÍ používat jinou metodu parsování** — pravděpodobně:
- Forward scan přes všech 257 bloků
- Či backward scan s vyšším max k

### Nález B: První funkční VCF používal COLOR AT OFFSET 12

| Verze | Color offset | Hodnota |
|-------|-------------|---------|
| Pracovní (`4ba9446`) | **12** | 0x00FFFFFF (BGR bílá) |
| Nativní (`square_1_aci`) | 12 | 0x00000000 (BGR černá) |
| Současný syntetický (HEAD) | **76** | 0x00000000 (vždy černá) |

VCutWorks pravděpodobně čte barvu vrstvy z **offsetu 12** layer bloku. Současný writer ji ukládá na offset 76 (a na offsetu 12 má GEOMETRY_HEADER_TEMPLATE data = různá čísla). To může způsobovat neshodu barvy → VCutWorks nespáruje geometrii s vrstvou.

### Nález C: Geometrie měla v pracovní verzi JINOU strukturu

| Vlastnost | Pracovní (`4ba9446`) | Nativní (`square_1_aci`) | Současný (HEAD) |
|-----------|---------------------|--------------------------|-----------------|
| Bytes 12-44 geometrie | **nuly** | **nuly** | **GEOMETRY_HEADER_TEMPLATE** (4×1.0 float) |
| Circle pt_count | 1 | 1 (?) | **4** |
| Trailer | **NENÍ (jen h+b)** | **ANO (285 B)** | **ANO (h+b+t)** |
| MACHINE_PROFILE | **NE** | **ANO (418 B)** | **ANO (418 B)** |

### Nález D: Žádný reader nenašel vrstvy v pracovním VCF

- Backward reader (`4ba9446`): 0 layers
- Forward reader (`5ce3e80`): 0 layers
- **Současný reader** (HEAD): 1 layer (v aktuálním syntetickém VCF)

**Roundtrip testy jsou tedy samovolně validní, ale irelevantní pro VCutWorks** — testují, zda náš čte náš writer, ne zda VCutWorks čte náš writer.

---

## 5. HLAVNÍ HYPOTÉZY — CO ZPŮSOBILO SELHÁNÍ

### H1 — Missing/posunutá barva na offsetu 12 ⭐⭐⭐⭐⭐

V pracovní verzi byla barva na offsetu 12. VCutWorks ji tam četl a spároval s geometrickou barvou. Po commitu `ed867c1` je barva na offsetu 76 a na offsetu 12 jsou data z GEOMETRY_HEADER_TEMPLATE (různá čísla). VCutWorks čte "barvu" 0x00000000 (z TEMPLATE startu) nebo 0x00000000 → vždy nula → geometrie se nespáruje s vrstvou → nezobrazí se.

**Kontrola:** Zapsat barvu zpět na offset 12 (a zároveň ji ponechat i v linked-list pointeru na offsetu 606).

### H2 — GEOMETRY_HEADER_TEMPLATE (bytes 12-44 geometrie) ⭐⭐⭐⭐

Pracovní verze i nativní mají v geometrii na bytech 12-44 **nuly**. Současný writer tam zapisuje GEOMETRY_HEADER_TEMPLATE (čtyři float64 hodnoty 1.0). VCutWorks může tato data interpretovat jako souřadnicový offset a zahodit element.

**Kontrola:** Vynechat GEOMETRY_HEADER_TEMPLATE (ponechat bytes 12-44 jako nuly), otestovat v GUI.

### H3 — Trailer interference ⭐⭐⭐

Pracovní verze trailer NEZAPISOVALA (pouze h + b). Současná verze přidává 199 B prefix + DXF cestu. VCutWorks může očekávat trailer až od specifického offsetu spojeného s 0xD7.

### H4 — Počet segmentů kruhu ⭐⭐

Circle element měl v pracovní verzi pt_count=1. Současný má pt_count=4 (4 segmenty). Native má pravděpodobně také 1.

---

## 6. DOPORUČENÝ POSTUP — ITERATIVNÍ NÁVRAT K FUNKČNOSTI

1. **Krok 1:** Vytvořit syntetický VCF s layoutem z `4ba9446`
   - aktivní blok LAST (současný layout)
   - color na offsetu 12 (JAKO v 4ba9446, ne na 76)
   - GEOMETRY_HEADER_TEMPLATE vynechat (nuly v 12-44)
   - bez MACHINE_PROFILE (jen 53 B preamble)
   - bez traileru (jen h+b)
   - linked-list zachovat (je v nativním)
   - otestovat v GUI

2. **Krok 2:** Pokud funguje, přidávat jednu změnu po druhé (binární hledání):
   - Přidat MACHINE_PROFILE → test
   - Přidat trailer → test
   - Přidat GEOMETRY_HEADER_TEMPLATE → test
   - Změnit color z offsetu 12 na linked-list only → test

3. **Krok 3:** Po každé změně hex-diff proti nativnímu VCF a redukovat počet diff regionů

---

## 7. ZÁVĚR

První funkční VCF (`4ba9446`) se lišil od současného v **minimálně 9 strukturních vlastnostech**. Nejpravděpodobnější příčina ztráty funkčnosti je přesun barvy z **offsetu 12** na **offset 76** (commit `ed867c1`) a přidání **GEOMETRY_HEADER_TEMPLATE** (commit `a1b339c`).

**Nejvyšší priorita:** Obnovit barvu na offset 12 layer bloku (testovat samostatně v GUI).

**Náš reader/roundtrip testy jsou nespolehlivé** — procházejí, protože aktuální reader používá linked-list (pos-4), zatímco VCutWorks pravděpodobně čte barvu z offsetu 12. To je potřeba zohlednit při dalším vývoji.
