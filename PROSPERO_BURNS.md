# Prospero Burns – campaign fork

This is a fork of [BSData/horus-heresy-3rd-edition](https://github.com/BSData/horus-heresy-3rd-edition) with the house rules from the *Prospero Burns – Ashes of the City of Light* campaign pack added, so the group can build campaign lists in New Recruit.

## Using it in New Recruit

1. In New Recruit, add a game system from GitHub and give it this repo: `crazymunch/hhv3-prospero-burns`.
2. The system shows as **Horus Heresy 3rd Edition - Prospero Burns**.
3. Build lists as normal. The campaign additions appear alongside the official entries.

BattleScribe can't read this repo: the data is in New Recruit's JSON format.

## What's added

| Addition | Where it appears | Notes |
|---|---|---|
| Campaign Doctrine: The Axis of Dissolution | Thousand Sons army, Army Configuration (next to Rite of War) | Optional, max 1. Its Troops and Armour limits are **not** checked automatically. |
| Campaign Doctrine: The Pale Hunters | Space Wolves army, Army Configuration | Optional, max 1. Shows an error if the detachment has a Fortification or more than one Armour unit. Drop pods and Dreadclaws are not checked. |
| Venator Ignitum (Prospero Burns) | Upgrade on the Warhound Titan (Legio Titanicus) | 0 pts, max 1. Carries the Canis Vertex and Dying Engine rules. |
| Dreadnought Talon house ruling | Auxiliary – Dreadnought Talon (needs a Mortificator) | Any Contemptor- or Castra Ferrum-chassis Dreadnought can fill the Talon's slots: Contemptor, Castra Ferrum, Contemptor-Osiron (Thousand Sons), Contemptor-Incaendius (Blood Angels). The slot keeps its official name, "Contemptor Dreadnoughts Only". |
| Spireguard Templar Section | Solar Auxilia, Elites | Hidden unless the army has the Prosperine Spireguard designation. 110 pts for 10, +10 per extra Templar, up to 20. Playtest points. |

Every object the campaign adds is tagged `"comment": "Prospero Burns campaign"`. The only official line changed is the game system's display name.

## Keeping up to date with the official data

1. On GitHub, use **Sync fork** to pull in the latest official changes.
2. If GitHub reports a conflict, discard our side of the conflicted files (take upstream), then re-apply the campaign entries:
   ```
   python3 tools/prospero_burns.py
   ```
   The script is idempotent: it removes anything tagged for the campaign and adds it back, keeping the IDs the same. `tools/nrjson.py` writes files in exactly the same layout as the New Recruit editor, so diffs stay small.
3. Commit and push. The New Recruit refresh workflow runs on every push to `main`.

To change a rule's wording or a cost, edit `tools/prospero_burns.py` and re-run it rather than hand-editing the JSON.
