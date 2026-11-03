# Fridgeroo on Tour — series bible

**Fridgeroo** (the white fridge with sunglasses and a red cape, grumpy-grandpa voice) hops from house to house rescuing fridges. **Every part = a new house, a new resident, a new look and ONE app feature.** Each part must make sense on its own (most viewers only ever see one part); "PART X" is a bonus.

## Episode recipe (13–17 s)
| Beat | Time | What |
|---|---|---|
| Disaster | 0–2.5 s | `tour` + `burst` (or a new disaster action): the problem is visible and loud in frame 1. "PART X" badge + 🚨 label. |
| Crash-in | 2.5–4.8 s | `arrive`: the house door bursts open, debris, Fridgeroo hops in (3 hops). First line, heroic or sarcastic. |
| Roast | 4.8–7.7 s | `herocam` → `hstare`: he roasts the resident, then stares at the viewer ("Yeah, YOU."). |
| The fix | 7.7–10.8 s | `holo` (+ `restore` or a feature-specific action): the hologram app shows THIS episode's feature solving THIS problem (`appRows`, `notif`). |
| Payoff | 10.8–13 s | `celebrate` + `shades` + `magic`: the house fridge gets sunglasses too, sky of fridges, "FRIDGE SAVED ✅". |
| Teaser | 13–14.6 s | `teaser:{next:"<next house>", part:N+1}` — must match the next row below. |
| End card | 1.8 s | "Use it or lose it." |

Plan fields: `tour:true`, `part`, `look`, `cast` (hoodie, hair, skin, acc: cap | headphones | glasses | bun, accColor), `pos` {stu:[x,z], yaw, hero:[x,z]}, `spill` items, `appRows`. Start every part from `voxelplans/tour-01-fridge-explodes.json`.
Voice lines are spoken by the hero: `voice:{who:'hero', src:'hero', a, b, at}` (voice file key "hero").

## Episode list (update the status column; bots may improve premises, never repeat one)
| Part | House | Problem / crazy premise | Feature | Look | Resident | Status |
|---|---|---|---|---|---|---|
| 1 | Student house | The fridge is so overstuffed it explodes | Expiry alerts ("goes off tomorrow") | toon | orange hoodie, headphones | built (needs voice) |
| 2 | The freezer from hell 🧊 | An ice-age freezer: a 2019 pizza frozen in a giant ice block | Freezer tracking | neon | dad with glasses | planned |
| 3 | The party flat 🎉 | The receipt is so long it rolls out across the whole floor | Receipt scan | clay | girl with a bun | planned |
| 4 | The gym bro's kitchen 💪 | 14 identical unlabeled tubs — which one is chicken? | Barcode scan + tags | voxel | guy with a cap | planned |
| 5 | The shared house ⚔️ | Housemate shelf war: name tags, food crossing borders | Shared home | toon | two housemates (add if possible) | planned |
| 6 | "Nothing to eat" flat 🍜 | Full fridge, he still orders takeaway | Recipes from what you have | clay | hoodie, no accessory | planned |
| 7 | The triple-milk house 🥛 | Milk bought three times — police line-up of cartons | Shopping list that knows what you have | neon | glasses | planned |
| 8 | The 2 p.m. breakfast 🥣 | Cereal at 2 p.m. while eggs go off | Morning breakfast idea notification | voxel | headphones | planned |
| 9 | The €300 bin 💸 | The bin is eating his money (coins pour in) | € saved + no-waste streak | toon | cap | planned |
| 10 | Hands-full house 🛍️ | Arms full of groceries, can't type | Voice add | clay | bun | planned |
| 11 | The cupboard of 2021 🥫 | A can older than his degree | Cupboard tracking | neon | glasses | planned |
| 12 | Leftovers reality show 📺 | Containers vote each other out | Ate it / Binned it buttons | voxel | headphones | planned |
After part 12, start "Season 2" with new houses (a grandma, a couple, a dorm floor…) — the same rules.
