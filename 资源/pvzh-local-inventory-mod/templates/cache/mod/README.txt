PVZH Mod — local inventory extra
================================

Place this folder at:

  Android/data/com.ea.gp.pvzheroes/files/cache/mod/

File: inventory_extra.json
  - Declares cards/heroes you own for LOCAL play.
  - Requires PVZH Mod Base (patched libil2cpp.so).
  - Does NOT upload custom cards to official servers.

Schema and rules:
  See project docs/inventory_extra_spec.md

Quick example:

{
  "schemaVersion": 1,
  "Cards": {
    "90001": 4
  },
  "Heroes": {}
}

Card definitions still come from card_data cache mods.
IDs in this file must match card_data Guids.
