# PvZ Heroes Phantom Engine / 幻影引擎

**Version:** 2.1  

A desktop GUI tool for **Plants vs. Zombies Heroes** card modding: edit card JSON fields, build ability logic trees, manage multi-card projects (`.phantom`), and inject changes into Unity AssetBundles.

中文界面 + English UI（主题设置页一键切换）。

---

## Features

| Area | Description |
|------|-------------|
| **Projects** | Multiple `.phantom` mods, card roster, dirty-save prompts |
| **Basic** | GUID, cost, attack/health, faction, set, flags, UI ability tags, affinities |
| **Subtypes / Tags** | Logic vs display layers, custom subtype library, tag library |
| **Abilities** | Component abilities + granted triggered abilities (e.g. double strike / overshoot) |
| **Logic editor** | Visual tree: triggers → filters → targets → effects; undo/redo; presets |
| **Export** | Inject all project cards into the game `cards` TextAsset / bundle |
| **Theme + Language** | Multiple themes; **中文 / English** shell UI |
| **Help** | In-app guide (matches this README in spirit) |

---

## Requirements

- **Python** 3.10+ (tested on 3.13 / 3.14)
- **Windows** recommended (path defaults and batch launcher)
- Dependencies:

```bash
pip install -r requirements.txt
```

Packages:

- `PySide6` — GUI  
- `UnityPy` — AssetBundle read/write  

---

## Run

```bash
pip install -r requirements.txt
python main.py
```

Or double-click `开始.bat` (Windows).

Optional local data (not shipped in this repo — place your own copies):

- `data/card_data_5` — original AB / raw bundle (for export inject)  
- `data/card_data_5.json` — optional JSON pool for import  
- `uuid.txt` — known card GUID → display name (included for offline lookup)  

All paths resolve from the **application directory** (where `main.py` lives), not the process CWD.

---

## Quick workflow

1. **Projects** → create / open a `.phantom` project  
2. New card or import from JSON (Basic tab)  
3. Edit Basic / Subtypes / Tags / Abilities / Logic  
4. **Ctrl+S** — save into project  
5. **Export** — set In/Out paths → build mod bundle  
6. Deploy output with your mod loader  

### Shortcuts

| Key | Action |
|-----|--------|
| Ctrl+S | Save card to project |
| Ctrl+E | Export pack |
| Ctrl+Z / Ctrl+Y / Ctrl+Shift+Z | Logic undo / redo (focus in Logic tab) |
| Ctrl+C / Ctrl+V | Logic node copy / paste |
| Delete | Delete logic nodes |

---

## Language (i18n)

- Switch on **Theme** tab: **中文** / **English**  
- Preference stored in `QSettings` (`language`)  
- Implementation: `i18n.py` + each tab’s `retranslate_ui()`  
- Skill **node library**, param/enum labels, palette subcategories, and NL ability text: `localization.py` + `logic_translator.py` (follow current language)  
- Palette search matches both display labels and engine class names (`DamageEffect`, etc.)

---

## Project layout

```text
.
  main.py              # entry
  ui_main.py           # main window
  i18n.py              # UI zh/en strings
  card_model.py        # card ↔ engine JSON
  project_manager.py   # .phantom projects
  bundle_packer.py     # UnityPy inject
  logic_library.py     # ability node definitions
  logic_translator.py  # NL description of abilities
  localization.py      # node/param/enum display names (zh+en)
  config.py            # rarities, subtypes, paths
  ui/                  # tabs + logic editor
  data/                # local game dumps only (gitignored)
  projects/            # user projects (gitignored)
  out/                 # export output (gitignored)
  requirements.txt
  README.md
  LICENSE
```

---

## Known limitations

- Ability **natural-language** descriptions cover common components; exotic nodes may show simplified text  
- Unknown engine components are kept as raw nodes and re-exported as-is  
- Export overwrites matching GUIDs inside the target `cards` blob  

---

## License / credit

Personal / community modding tool for PvZ Heroes.  
Game assets and trademarks belong to their respective owners.  
Use only with data you are allowed to modify.

---

## Changelog (recent)

- **v2.1** — Bugfix batch (GUID ghost, subtypes crash, undo/redo, paths, translator Descriptor); UI i18n zh/en; Help tab; README  
- **v2.1+** — Full skill-node EN localization (palette, inspector, NL descriptions); language switch refreshes node labels

---

Happy modding / 祝改卡顺利！
