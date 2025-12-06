# EDHREC Commander Menu - Hierarchical Structure

## ✅ Complete

Successfully created hierarchical menu structure matching EDHREC's commander navigation.

---

## Output File

**Location:** `data_sources_comprehensive/edhrec_commander_menu_hierarchical.json`

**Size:** 4,254 bytes

---

## Structure Summary

### 7 Top-Level Categories

1. **Top Commanders** - Link to main commanders page
2. **Partners** - Link to partners page
3. **Mono** - 6 subcategories (mono-colored + colorless)
4. **2 Color** - 10 subcategories (guilds)
5. **3 Color** - 10 subcategories (shards + wedges)
6. **4 Color** - 5 subcategories (nephilim)
7. **5 Color** - 1 subcategory

**Total Subcategories:** 32

---

## Hierarchy Breakdown

### Mono Colors (6)
- Mono White
- Mono Blue
- Mono Black
- Mono Red
- Mono Green
- Colorless

### 2-Color Guilds (10)
- **Azorius** (White-Blue)
- **Dimir** (Blue-Black)
- **Rakdos** (Black-Red)
- **Gruul** (Red-Green)
- **Selesnya** (Green-White)
- **Orzhov** (White-Black)
- **Izzet** (Blue-Red)
- **Golgari** (Black-Green)
- **Boros** (Red-White)
- **Simic** (Green-Blue)

### 3-Color Combinations (10)

**Shards (5):**
- **Esper** (White-Blue-Black)
- **Grixis** (Blue-Black-Red)
- **Jund** (Black-Red-Green)
- **Naya** (Red-Green-White)
- **Bant** (Green-White-Blue)

**Wedges (5):**
- **Abzan** (White-Black-Green)
- **Jeskai** (Blue-Red-White)
- **Sultai** (Black-Green-Blue)
- **Mardu** (Red-White-Black)
- **Temur** (Green-Blue-Red)

### 4-Color Combinations (5)
- **Yore Tiller** (WUBR - no Green)
- **Glint Eye** (UBRG - no White)
- **Dune Brood** (BRGW - no Blue)
- **Ink Treader** (RGWU - no Black)
- **Witch Maw** (GWUB - no Red)

### 5-Color (1)
- **Five Color** (WUBRG - all colors)

---

## JSON Schema

### Top-Level Structure

```json
{
  "menu": "Commanders",
  "source": "EDHREC",
  "extracted_at": "ISO-8601 timestamp",
  "categories": [...]
}
```

### Category with No Submenu

```json
{
  "name": "Top Commanders",
  "url": "https://edhrec.com/commanders",
  "has_submenu": false
}
```

### Category with Submenu

```json
{
  "name": "2 Color",
  "has_submenu": true,
  "subcategories": [
    {
      "name": "Azorius",
      "url": "https://edhrec.com/commanders/azorius"
    },
    ...
  ]
}
```

---

## Visual Tree Structure

```
📁 Commanders Menu
│
├─ 📄 Top Commanders → https://edhrec.com/commanders
│
├─ 📄 Partners → https://edhrec.com/partners
│
├─ 📁 Mono (6 subcategories)
│  ├─ Mono White → /commanders/mono-white
│  ├─ Mono Blue → /commanders/mono-blue
│  ├─ Mono Black → /commanders/mono-black
│  ├─ Mono Red → /commanders/mono-red
│  ├─ Mono Green → /commanders/mono-green
│  └─ Colorless → /commanders/colorless
│
├─ 📁 2 Color (10 subcategories - Guilds)
│  ├─ Azorius → /commanders/azorius
│  ├─ Dimir → /commanders/dimir
│  ├─ Rakdos → /commanders/rakdos
│  ├─ Gruul → /commanders/gruul
│  ├─ Selesnya → /commanders/selesnya
│  ├─ Orzhov → /commanders/orzhov
│  ├─ Izzet → /commanders/izzet
│  ├─ Golgari → /commanders/golgari
│  ├─ Boros → /commanders/boros
│  └─ Simic → /commanders/simic
│
├─ 📁 3 Color (10 subcategories - Shards + Wedges)
│  ├─ Esper → /commanders/esper
│  ├─ Grixis → /commanders/grixis
│  ├─ Jund → /commanders/jund
│  ├─ Naya → /commanders/naya
│  ├─ Bant → /commanders/bant
│  ├─ Abzan → /commanders/abzan
│  ├─ Jeskai → /commanders/jeskai
│  ├─ Sultai → /commanders/sultai
│  ├─ Mardu → /commanders/mardu
│  └─ Temur → /commanders/temur
│
├─ 📁 4 Color (5 subcategories - Nephilim)
│  ├─ Yore Tiller → /commanders/yore-tiller
│  ├─ Glint Eye → /commanders/glint-eye
│  ├─ Dune Brood → /commanders/dune-brood
│  ├─ Ink Treader → /commanders/ink-treader
│  └─ Witch Maw → /commanders/witch-maw
│
└─ 📁 5 Color (1 subcategory)
   └─ Five Color → /commanders/five-color
```

---

## Usage Examples

### Frontend Navigation

```typescript
// Load menu structure
import menuData from './edhrec_commander_menu_hierarchical.json';

// Render dropdown menu
menuData.categories.forEach(category => {
  if (category.has_submenu) {
    // Render expandable menu
    renderDropdown(category.name, category.subcategories);
  } else {
    // Render direct link
    renderLink(category.name, category.url);
  }
});
```

### Find Specific Color Combination

```python
import json

with open('edhrec_commander_menu_hierarchical.json') as f:
    menu = json.load(f)

# Find all 2-color guilds
two_color = next(cat for cat in menu['categories'] if cat['name'] == '2 Color')
guilds = [sub['name'] for sub in two_color['subcategories']]

print(guilds)
# ['Azorius', 'Dimir', 'Rakdos', 'Gruul', 'Selesnya', 
#  'Orzhov', 'Izzet', 'Golgari', 'Boros', 'Simic']
```

### Generate URL for Color Combination

```python
# Find URL for Azorius commanders
for category in menu['categories']:
    if category.get('has_submenu'):
        for subcat in category['subcategories']:
            if subcat['name'] == 'Azorius':
                print(subcat['url'])
                # https://edhrec.com/commanders/azorius
```

---

## Files

1. **Input:** `data_sources_comprehensive/edhrec_full/edhrec_full_20251204_071721.json`
   - Flat list of 32 commander color combinations

2. **Script:** `scripts/create_hierarchical_menu.py`
   - Converts flat list to hierarchical structure
   - Organizes by color identity

3. **Output:** `data_sources_comprehensive/edhrec_commander_menu_hierarchical.json`
   - Hierarchical menu structure (4,254 bytes)
   - 7 top-level categories
   - 32 subcategories

---

## Statistics

| Category | Subcategories | Description |
|----------|--------------|-------------|
| Top Commanders | - | Main commanders page |
| Partners | - | Partner commanders |
| Mono | 6 | Single-color + colorless |
| 2 Color | 10 | Two-color guilds |
| 3 Color | 10 | Shards (5) + Wedges (5) |
| 4 Color | 5 | Nephilim (missing one color each) |
| 5 Color | 1 | All five colors |
| **Total** | **32** | All color combinations |

---

## Color Identity Reference

### Color Abbreviations
- **W** = White
- **U** = Blue
- **B** = Black
- **R** = Red
- **G** = Green

### Guild Names (2-Color)
| Guild | Colors | Identity |
|-------|--------|----------|
| Azorius | W/U | White-Blue |
| Dimir | U/B | Blue-Black |
| Rakdos | B/R | Black-Red |
| Gruul | R/G | Red-Green |
| Selesnya | G/W | Green-White |
| Orzhov | W/B | White-Black |
| Izzet | U/R | Blue-Red |
| Golgari | B/G | Black-Green |
| Boros | R/W | Red-White |
| Simic | G/U | Green-Blue |

---

**Status:** ✅ COMPLETE

Hierarchical commander menu structure created and saved.
