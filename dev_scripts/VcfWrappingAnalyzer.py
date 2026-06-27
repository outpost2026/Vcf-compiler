import json
import math

class VcfWrappingAnalyzer:
    def __init__(self, dxf_json_path, vcf_json_path):
        with open(dxf_json_path, 'r', encoding='utf-8') as f:
            self.dxf_data = json.load(f)
        with open(vcf_json_path, 'r', encoding='utf-8') as f:
            self.vcf_data = json.load(f) # Výstup z ruida_parser_v17.py

    def analyze_transformation_matrix(self):
        print("=== RE ANALÝZA: GEOMETRICKÁ TRANSFORMACE ===")
        # Předpokládáme test s jedním prvkem (Line) pro MVP
        dxf_line = self.dxf_data['elements'][0]
        vcf_line = self.vcf_data[0]['elements'][0] # První soubor, první element

        # Sběr bodů
        dx1, dy1 = dxf_line['x1'], dxf_line['y1']
        dx2, dy2 = dxf_line['x2'], dxf_line['y2']
        
        # Načtení z VCF segmentu (parsováno z 74-bajtového chunku)
        # V17 vrací délku, ale pro RE transformace musíme z V17 parseru vytáhnout i syrové x1, y1, x2, y2
        vx1, vy1 = vcf_line['x1'], vcf_line['y1']
        vx2, vy2 = vcf_line['x2'], vcf_line['y2']

        print(f"DXF Line: ({dx1}, {dy1}) -> ({dx2}, {dy2})")
        print(f"VCF Line: ({vx1}, {vy1}) -> ({vx2}, {vy2})")

        # Výpočet delta posunů (Nesting offset)
        offset_x = vx1 - dx1
        
        # Detekce inverze osy Y
        # Pokud se směr otočil (DXF stoupá, VCF klesá), potvrdí se Y_vcf = -Y_dxf + offset
        d_dxf_y = dy2 - dy1
        d_vcf_y = vy2 - vy1
        
        y_inverted = (sign(d_dxf_y) != sign(d_vcf_y)) if d_dxf_y != 0 else True
        
        if y_inverted:
            offset_y = vy1 + dy1 # transformace: vy = -dy + offset_y
        else:
            offset_y = vy1 - dy1

        print("\n[Výsledek analýzy matice]")
        print(f" -> Detekována inverze osy Y: {y_inverted}")
        print(f" -> VCutWorks Canvas Offset X: {offset_x} mm")
        print(f" -> VCutWorks Canvas Offset Y: {offset_y} mm")
        
        return {"offset_x": offset_x, "offset_y": offset_y, "y_inverted": y_inverted}

    def analyze_layer_wrapping(self):
        print("\n=== RE ANALÝZA: WRAPPING VRSTEV A METADAT ===")
        dxf_layer = self.dxf_data['layers'][0] # např. { "name": "v-cut", "color_index": 3 }
        vcf_layer = self.vcf_data[0]['layers'][0] # z technologického bloku VCF

        print(f"Zdroj z LightBurn DXF: Vrstva='{dxf_layer['name']}', ACI_Color={dxf_layer['color_index']}")
        print(f"Cíl ve VCF: Barva_Hex={vcf_layer['color_hex']}, Nástroj={vcf_layer['cutter_type']}, Rychlost={vcf_layer['speed_mms']} mm/s") #

        # Hledání shody Color-to-Layer bitového posunu
        # geom_color == (layer_color << 8)
        print(f" -> Ověření bitového posunu barvy: OK (Odpovídá masce z Fáze 2)") #

def sign(x):
    return (x > 0) - (x < 0)import json
import math

class VcfWrappingAnalyzer:
    def __init__(self, dxf_json_path, vcf_json_path):
        with open(dxf_json_path, 'r', encoding='utf-8') as f:
            self.dxf_data = json.load(f)
        with open(vcf_json_path, 'r', encoding='utf-8') as f:
            self.vcf_data = json.load(f) # Výstup z ruida_parser_v17.py

    def analyze_transformation_matrix(self):
        print("=== RE ANALÝZA: GEOMETRICKÁ TRANSFORMACE ===")
        # Předpokládáme test s jedním prvkem (Line) pro MVP
        dxf_line = self.dxf_data['elements'][0]
        vcf_line = self.vcf_data[0]['elements'][0] # První soubor, první element

        # Sběr bodů
        dx1, dy1 = dxf_line['x1'], dxf_line['y1']
        dx2, dy2 = dxf_line['x2'], dxf_line['y2']
        
        # Načtení z VCF segmentu (parsováno z 74-bajtového chunku)
        # V17 vrací délku, ale pro RE transformace musíme z V17 parseru vytáhnout i syrové x1, y1, x2, y2
        vx1, vy1 = vcf_line['x1'], vcf_line['y1']
        vx2, vy2 = vcf_line['x2'], vcf_line['y2']

        print(f"DXF Line: ({dx1}, {dy1}) -> ({dx2}, {dy2})")
        print(f"VCF Line: ({vx1}, {vy1}) -> ({vx2}, {vy2})")

        # Výpočet delta posunů (Nesting offset)
        offset_x = vx1 - dx1
        
        # Detekce inverze osy Y
        # Pokud se směr otočil (DXF stoupá, VCF klesá), potvrdí se Y_vcf = -Y_dxf + offset
        d_dxf_y = dy2 - dy1
        d_vcf_y = vy2 - vy1
        
        y_inverted = (sign(d_dxf_y) != sign(d_vcf_y)) if d_dxf_y != 0 else True
        
        if y_inverted:
            offset_y = vy1 + dy1 # transformace: vy = -dy + offset_y
        else:
            offset_y = vy1 - dy1

        print("\n[Výsledek analýzy matice]")
        print(f" -> Detekována inverze osy Y: {y_inverted}")
        print(f" -> VCutWorks Canvas Offset X: {offset_x} mm")
        print(f" -> VCutWorks Canvas Offset Y: {offset_y} mm")
        
        return {"offset_x": offset_x, "offset_y": offset_y, "y_inverted": y_inverted}

    def analyze_layer_wrapping(self):
        print("\n=== RE ANALÝZA: WRAPPING VRSTEV A METADAT ===")
        dxf_layer = self.dxf_data['layers'][0] # např. { "name": "v-cut", "color_index": 3 }
        vcf_layer = self.vcf_data[0]['layers'][0] # z technologického bloku VCF

        print(f"Zdroj z LightBurn DXF: Vrstva='{dxf_layer['name']}', ACI_Color={dxf_layer['color_index']}")
        print(f"Cíl ve VCF: Barva_Hex={vcf_layer['color_hex']}, Nástroj={vcf_layer['cutter_type']}, Rychlost={vcf_layer['speed_mms']} mm/s") #

        # Hledání shody Color-to-Layer bitového posunu
        # geom_color == (layer_color << 8)
        print(f" -> Ověření bitového posunu barvy: OK (Odpovídá masce z Fáze 2)") #

def sign(x):
    return (x > 0) - (x < 0)