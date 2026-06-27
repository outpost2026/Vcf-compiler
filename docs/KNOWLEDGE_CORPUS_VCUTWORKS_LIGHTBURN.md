# Knowledge Corpus: VCutWorks (.VCF) a LightBurn (.DXF) – Parsování geometrie, barev a vrstev

**Verze:** 1.0  
**Autor:** Reverse Engineering Synthesis (VCF Parser B2B v20–v21 + DXF Indexer v2.2–v2.4)  
**Pokrývá:** .VCF (Ruida/VCutWorks), .DXF (LightBurn export), vazba mezi formáty, barevné mapování, geometrické primitivy

---

## 1. Základní princip: Barva řídí vše

Barva je **primární klíč** pro přiřazení geometrického elementu k technologické vrstvě v obou formátech. Parser musí vždy nejprve extrahovat barvu elementu a na jejím základě určit vrstvu, nástroj a řezné parametry.

| Formát | Jak je barva uložena | Kam se mapuje |
|--------|----------------------|---------------|
| **.VCF** | `geom_color` (uint32) na offsetu +8 od magické signatury | `layer_color` bitovým posunem: `geom_color == (layer_color << 8)` |
| **.DXF (LightBurn)** | ACI index (0–255) nebo `true_color` (RGB) | LightBurn 32barevná CAM paleta přes euklidovskou interpolaci |

---

## 2. .VCF (Ruida/VCutWorks) – Binární formát

### 2.1 Globální struktura souboru

```
┌─────────────────────────────────────────────┐
│ 1. ASCII hlavička + metadata                 │
│    "RDVCUTFILEVER1.0.013"                    │
│    DXF source path (Windows-1250)            │
│    user tags, font names                     │
├─────────────────────────────────────────────┤
│ 2. Hřbitov palet (20 systémových palet)      │
│    ~150-200 kB fixní režie, vždy přítomen    │
├─────────────────────────────────────────────┤
│ 3. Geometrický payload                       │
│    Sekvence elementů: 8B sig + header + N*74B│
├─────────────────────────────────────────────┤
│ 4. Sekce aktivních vrstev                    │
│    Posledních ~200-2000 B souboru            │
│    Každá vrstva: 120-150 B blok              │
└─────────────────────────────────────────────┘
```

### 2.2 Magická signatura geometrie

```
8 bajtů: 0x01 0x00 0x01 0x00 0x00 0xFF 0xFF 0xFF
```

Tato signatura se v souboru vyskytuje opakovaně – **jednou pro každý geometrický element**. Parser skenuje celý soubor a každý výskyt zpracovává jako samostatný element.

### 2.3 Hlavička elementu (57 B od začátku signatury)

| Offset | Velikost | Typ | Význam |
|--------|----------|-----|--------|
| +0 | 8 B | bytes | Magická signatura `01 00 01 00 00 FF FF FF` |
| +8 | 4 B | uint32 | **`geom_color`** – barva elementu (klíč pro mapování do vrstvy) |
| +12 | 4 B | uint32 | Neznámý (často 0) |
| +16–+44 | 29 B | - | Neznámá data |
| **+45** | **4 B** | **uint32** | **`type_id`**: 0=úsečka/polyline, 1=polygon/kružnice |
| **+49** | **4 B** | **uint32** | **`pt_count`**: počet 74B segmentů |
| **+53** | **4 B** | **uint32** | **`subtype`**: 3=kružnice (pouze pro type_id=1), 0=obecný polygon |

### 2.4 Segment geometrie (74 B každý)

Pro každý segment `i` od `0` do `pt_count-1`:

| Offset v segmentu | Velikost | Typ | Význam |
|-------------------|----------|-----|--------|
| +0–+13 | 14 B | - | Padding / metadata (překrývá se s hlavičkou pro i=0) |
| **+14** | **8 B** | **double (LE)** | **X1** (start oblouku / bod na obvodu) |
| **+22** | **8 B** | **double (LE)** | **Y1** (start oblouku / střed Y) |
| **+30** | **8 B** | **double (LE)** | **X2** (konec oblouku / střed X) |
| **+38** | **8 B** | **double (LE)** | **Y2** (konec oblouku / bod na obvodu) |
| +46–+73 | 28 B | - | Padding / nepoužito |

### 2.5 Typy geometrických elementů

| `type_id` | `subtype` | `pt_count` | Interpretace |
|-----------|-----------|------------|--------------|
| 0 | libovolný | 1 | **Line** (úsečka) |
| 0 | libovolný | ≥2 | **Polyline** (lomená čára / otevřená křivka) |
| 1 | ≠3 | libovolný | **Polygon** (uzavřený mnohoúhelník) |
| 1 | ==3 | 4 | **Circle** (kružnice – 4× 90° oblouk) |

### 2.6 Kružnice – speciální případ (kritické!)

VCF **neukládá kružnici jako center + radius**, ale jako **4 na sebe navazující 90° oblouky** (quadrant arc segments). Každý oblouk je reprezentován jedním 74B segmentem.

**Formát prvního segmentu (i=0):**
- `X1, Y1` = **startovní bod oblouku** (bod na obvodu)
- `X2, Y2` = **koncový bod oblouku** (proti směru hodin)

**Výpočet středu a poloměru:**
```
střed_X = X2  (end point X prvního segmentu)
střed_Y = Y1  (start point Y prvního segmentu)
poloměr = abs(X2 - X1)
délka  = 2 * π * poloměr
```

**⚠️ Častá chyba:** Bývalá regrese (V14–V15) brala `(X1, Y1)` jako střed, což posouvalo kružnici o `ΔX = poloměr` doleva.

### 2.7 Segmentová geometrie – univerzální parser

Pro všechny typy elementů platí univerzální smyčka:
```python
for i in range(pt_count):
    seg_offset = p + i * 74
    x1, y1 = unpack('<dd', data, seg_offset + 14)
    x2, y2 = unpack('<dd', data, seg_offset + 30)
    # Výpočet délky: přičíst euklidovskou vzdálenost (x1,y1)→(x2,y2)
```

Tento přístup funguje pro Line, Polyline i Polygon. Pro Circle se používá speciální výpočet 2πR.

### 2.8 Barevné mapování (Color → Layer) ve VCF

**Klíčový vztah:**
```python
geom_color == (layer_color << 8) & 0xFFFFFFFF
```

Kde:
- `geom_color`: uint32 na offsetu +8 od magické signatury elementu
- `layer_color`: uint32 barva vrstvy v koncové sekci

**Příklad:**
- `layer_color = 0x000000FF` (modrá, alpha=0, B=255)
- `geom_color = (0x000000FF << 8) & 0xFFFFFFFF = 0x0000FF00`
- Parser přiřadí element s `geom_color == 0x0000FF00` k vrstvě s `layer_color == 0x000000FF`

### 2.9 Technologické parametry vrstvy (koncová sekce)

Každá vrstva je blok ~120–150 B. Offsety relativní k `S` (začátek bloku rychlosti):

| Offset | Velikost | Typ | Význam |
|--------|----------|-----|--------|
| S-8 | 4 B | uint32 | **`layer_color`** (ARGB) |
| S-4 | 4 B | bytes | Signatura `0x01 0x00 0x00 0x00` |
| S+0 | 8 B | double | **Rychlost** (mm/s) |
| S+28 | 4 B | uint32 | **Cutter type** (maskovaný: horních 16b pokud nenulové, jinak dolních 16b) |
| S+76 | 8 B | double | **H1** – start height (mm) |
| S+84 | 4 B | uint32 | **Feed count** – počet průchodů |
| S+92 | 8 B | double | **H2** – end height (mm) |
| S+100 | 2 B | uint16 | **Direction** (pouze V-slot: 0=Left, 1=Right, 2=Both) |
| S+102 | 8 B | double | **V-slot width compensation** (mm) |
| S+110 | 8 B | double | **Starting extension** (mm) |
| S+118 | 8 B | double | **Ending extension** (mm) |

**Typy nástrojů (cutter_type):**
| Hodnota | Nástroj |
|---------|---------|
| 0 | Vibrate cutter (oscilační nůž) |
| 1 | Wheel (kolečko) |
| 2 | Milling (fréza) |
| 3 | V-slot (V-drážka) |
| 4 | Vibrate cut (alternativní) |

### 2.10 Export flag (Output Yes/No)

Vrstvy mohou být označeny jako `Output=No` (pouze vizuální vrstva – např. rytí, gravírování) nebo `Output=Yes` (aktivní řezná vrstva). Flag je 32-bit int v koncové sekci.

---

## 3. .DXF (LightBurn export) – ACI barvy a CAM paleta

### 3.1 Problém: LightBurn ≠ AutoCAD

LightBurn při exportu do DXF **nepoužívá standardní AutoCAD ACI→RGB mapování**. Místo toho používá vlastní 32barevnou CAM paletu. Standardní AutoCAD barvy (např. ACI 4 = cyan) se neshodují s LightBurn (ACI 4 → C06/140).

### 3.2 LightBurn 32barevná CAM paleta (ground truth)

Kompletní paleta použitá pro euklidovskou interpolaci:

```python
LIGHTBURN_CAM_PALETTE = [
    (R, G, B, cam_layer_index, aci), ...
]
```

| Index | Barva | ACI | RGB | Použití |
|-------|-------|-----|-----|---------|
| C00 | Černá | 7 | (0,0,0) | Cut / obrysy |
| C01 | Modrá | 5 | (0,0,255) | Rytí / gravírování |
| C02 | Červená | 1 | (255,0,0) | Řez |
| C03 | Zelená | 3 | (0,224,0) | V-slot / drážky |
| C04 | Žlutá | 2 | (208,208,0) | Skórování |
| C05 | Oranžová | 30 | (255,128,0) | Speciální |
| C06 | Cyan | 140 | (0,224,224) | Izolace |
| C07 | Magenta | 6 | (255,0,255) | Test |
| C08 | Sv. šedá | 252 | (180,180,180) | - |
| C09 | Tm. modrá | 12 | (0,0,160) | - |
| C10 | Tm. červená | 14 | (160,0,0) | - |
| ... | ... | ... | ... | (plných 32 barev) |
| T1 | Nástroj 1 | 7 | (243,105,38) | Nástrojová vrstva |
| T2 | Nástroj 2 | 7 | (12,150,217) | Nástrojová vrstva |

### 3.3 ACI Color Resolver (resolve_cam_color)

Parser DXF používá třístupňové rozlišení barvy:

```
1. TRUE_COLOR (přes RGB)
   └─ Pokud entity.has_dxf_attrib('true_color'):
      └─ Extrahovat R,G,B → Euclidean match k LIGHTBURN_CAM_PALETTE → vrací ACI

2. ACI (přes color index)
   └─ Pokud entity.has_dxf_attrib('color'):
      └─ c == 0 nebo c == 7 → vrací 7 (Black)
      └─ c == 256 → pokračuje na vrstvu
      └─ jinak: aci2rgb(c) → Euclidean match → vrací ACI

3. VRSTVA (fallback)
   └─ doc.layers.get(entity.dxf.layer)
      └─ true_color → Euclidean match
      └─ color index → aci2rgb → Euclidean match
```

**Euklidovská interpolace:**
```python
def _closest_aci(r, g, b) -> int:
    min_dist = float('inf')
    best_aci = 7  # fallback na černou
    for pr, pg, pb, _, aci in LIGHTBURN_CAM_PALETTE:
        d = (pr - r)**2 + (pg - g)**2 + (pb - b)**2
        if d < min_dist:
            min_dist = d
            best_aci = aci
    return best_aci
```

### 3.4 ACI Priority pro přiřazení nástroje (C3 fix)

Pokud je ACI barva namapována v `tool_config["aci_color_mapping"]`, má **priorita přiřazení nástroje před geometrickou heuristikou**:

1. Zkontrolovat `aci_color_mapping[aci].cutter_type`
2. Pokud je definován → použít ho (i když je v konfliktu s geometrií)
3. Jinak → fallback na geometrickou heuristiku (uzavřené smyčky = vibrate, otevřené = V-slot)
4. Při konfliktu → nastavit `tool_conflict_detected = True`

### 3.5 INSERT bloky (Block explosion)

LightBurn export DXF často používá `INSERT` entity (bloky). Parser musí provést **explozi bloků**:

```python
if entity.dxftype() == 'INSERT':
    block = doc.blocks.get(entity.dxf.name)
    if block:
        for e in block:
            exploded = e.copy()
            transformace = entity.matrix_44()
            exploded.transform(transformace)
            zpracovat_jako_samostatný_entity(exploded)
```

Bez exploze bloků zůstane až 50 % geometrie neparsované.

---

## 4. Vazba VCF ↔ DXF (LightBurn pipeline)

### 4.1 Typická cesta dat

```
CAD (Illustrator / CorelDRAW)
  │
  ▼ (export DXF)
LightBurn
  │
  ▼ (import DXF + nastavení vrstev/barev)
LightBurn CAM
  │
  ▼ (export VCF)
VCutWorks (Ruida kontrolér)
  │
  ▼ (řezání)
CNC stroj
```

### 4.2 Co se děje při LightBurn → VCF exportu

1. LightBurn mapuje každou ze svých 32 CAM vrstev na ACI barvu
2. Při exportu DXF se ACI barvy uloží jako `color` (nebo `true_color`)
3. Při importu do VCutWorks se DXF převede do .VCF:
   - ACI barva → `geom_color` (s bitovým posunem `<< 8`)
   - `layer_color` v koncové sekci → odpovídá původní ACI barvě
   - Uzavřené křivky → Polygon (type_id=1)
   - Otevřené křivky → Polyline/Line (type_id=0)
   - Kružnice → 4 segmenty s subtype=3

### 4.3 Známé odchylky LightBurn od standardu

1. **ACI 4 není cyan** → LightBurn mapuje ACI 4 na C06 (RGB 0,224,224) místo standardního cyan
2. **ACI 202 není purple** → LightBurn mapuje ACI 202 na C15 (RGB 160,0,160)
3. **Sdílení ACI 7 (černá)** → Všechny nástrojové vrstvy T1 a T2 mají ACI=7
4. **true_color > ACI** → LightBurn preferuje true_color při exportu, a to je nutné resolvovat přes euklidovskou vzdálenost
5. **Block INSERT** → LightBurn používá bloky, které standardní DXF parsery ignorují

---

## 5. Parser implementace – kritické detaily

### 5.1 VCF Parser (v20–v21)

```python
# 1. Najít všechny výskyty magické signatury
while True:
    pos = binary_data.find(GEOMETRY_SIG, offset)
    if pos == -1: break

    # 2. Přečíst barvu elementu
    geom_color = unpack('<I', data, pos + 8)

    # 3. Mapovat do vrstvy
    for idx, layer in enumerate(layers):
        if geom_color == (layer["color_val"] << 8) & 0xFFFFFFFF:
            layer_index = idx; break

    # 4. Přečíst hlavičku geometrie
    p = pos + 45
    type_id, pt_count, subtype = unpack('<III', data, p)

    # 5. Iterovat segmenty
    for i in range(pt_count):
        seg = p + i * 74
        x1, y1 = unpack('<dd', data, seg + 14)
        x2, y2 = unpack('<dd', data, seg + 30)

    # 6. Speciální případ: Circle
    if type_id == 1 and (subtype & 0xFFFF) == 3:
        cx, cy = x2, y1  # NE (x1, y1)!
        radius = abs(x2 - x1)
```

### 5.2 DXF Parser (v2.2–v2.4)

```python
# 1. Otevřít DXF
doc = ezdxf.readfile(path)
msp = doc.modelspace()

# 2. Explodovat INSERT bloky
for entity in list(msp):
    if entity.dxftype() == 'INSERT':
        block = doc.blocks.get(entity.dxf.name)
        block_explode(msp, block, entity.matrix_44())

# 3. Zpracovat každou entitu
for entity in msp.query():
    color_idx = resolve_cam_color(entity, doc)
    dtype = entity.dxftype()
    if dtype not in GEOM_FNS: continue

    # 4. Extrahovat geometrii dle typu
    length, vertices = GEOM_FNS[dtype](entity)

    # 5. RDP zjednodušení (prah 1000 vrcholů)
    if len(vertices) > RDP_THRESHOLD_PTS:
        vertices = _rdp_simplify(vertices, RDP_EPSILON_MM)
```

---

## 6. Validace a ground truth

### 6.1 Testovací sada VCF

12 souborů v `demo_data/` pokrývajících:
- Jednoduché úsečky a polygony (obdélníky)
- Kružnice různých poloměrů
- Lomené čáry (polylines) s více segmenty
- Reálné výrobní motivy (botanic)
- Agregované soubory z více zakázek
- Speciální případy (PCB, ozubená kola)

Přesnost parseru: **>99,98 %** (odchylka <0,02 % oproti LightBurn měření).

### 6.2 Testovací sada DXF

7 souborů pokrývajících:
- Jednoduché tvary
- Slotové panely
- Složité PCB motivy
- INSERT bloky
- SPLINE křivky

Zlomové ACI barvy: `4→140(C06)`, `202→214(C15)`, `0/7→7(C00)`.

### 6.3 Metodika validace

1. Export .VCF → .DXF pomocí VCutWorks
2. Import do LightBurn
3. Měření délky elementů nástrojem Measure
4. Porovnání s výstupem parseru
5. Odchylka <0,02 % = PASS

---

## 7. Checklist pro debugging barev/vrstev

Při podezření na špatné mapování barev postupovat v tomto pořadí:

- [ ] **1.** Je `geom_color` na offsetu +8 od magické signatury správně načten jako uint32?
- [ ] **2.** Je `layer_color` v koncové sekci správně načten (S-8)?
- [ ] **3.** Platí `geom_color == (layer_color << 8) & 0xFFFFFFFF`?
- [ ] **4.** Je `color_val` v layer extraction správně načten (use `struct.unpack('<I')`)?
- [ ] **5.** Pokud DXF: je `true_color` správně extrahován a převeden na ACI?
- [ ] **6.** Pokud DXF: je euklidovská distance použita správně (všechny 3 RGB složky)?
- [ ] **7.** Jsou INSERT bloky explodovány?
- [ ] **8.** Je `pt_count` správně použit pro iteraci segmentů?
- [ ] **9.** Pro kružnice: je střed správně `(X2, Y1)` místo `(X1, Y1)`?
- [ ] **10.** Je dodržen little-endian pro všechny numeric typy?
- [ ] **11.** Jsou textová metadata v kódování Windows-1250 (nikoli UTF-8)?
- [ ] **12.** Pro agregované VCF: je prostorový split algoritmus validní?

---

## 8. Slovník pojmů

| Pojem | Význam |
|-------|--------|
| **VCF** | Ruida VCut File – binární CAM formát pro CNC stroje s Ruida kontrolérem |
| **VCutWorks** | CAM software pro Ruida kontroléry (import DXF, export VCF) |
| **LightBurn** | CAD/CAM software pro laserové a CNC stroje (používán jako DXF editor) |
| **geom_color** | 32-bit barva uložená u každého geometrického elementu ve VCF |
| **layer_color** | 32-bit ARGB barva technologické vrstvy v koncové sekci VCF |
| **ACI** | AutoCAD Color Index (0–255) |
| **true_color** | 24-bit RGB barva v DXF (24-bit, žádná paleta) |
| **CAM paleta** | LightBurn 32barevná paleta pro mapování ACI→nástroj |
| **Euklidovská interpolace** | Hledání nejbližší barvy v paletě pomocí minimalizace `(ΔR)²+(ΔG)²+(ΔB)²` |
| **Segment** | 74B blok ve VCF obsahující 4 double souřadnice (X1,Y1,X2,Y2) |
| **pt_count** | Počet segmentů v geometrickém elementu |
| **INSERT blok** | DXF entita odkazující na definici bloku (nutná exploze) |
| **RDP** | Ramer-Douglas-Peucker – algoritmus pro zjednodušení křivky |
| **Hřbitov palet** | 20 nepoužitých systémových palet ve VCF (balast ~150-200 kB) |
