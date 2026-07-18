# Tabletop Tavern Modding Guide

Tabletop Tavern supports mods that override unit stats, faction colors, hero data, and hero/faction battle bonuses — no code required, just plain text files. This guide covers the file formats. See the [`ExampleMod/`](ExampleMod/) folder for a complete, working example you can copy and edit.

## Where mods go

Mods live in a `Mods` folder inside the game's save data folder:

- **Windows:** `%USERPROFILE%\AppData\LocalLow\MemoriStudios\TabletopTavern\Mods\`

Each mod is its own subfolder:

```
Mods/
    MyModName/
        mod.json              <- required
        unit_overrides.json   <- optional
        race_overrides.json   <- optional
        hero_overrides.json   <- optional
        hero_bonus_rules.json <- optional
```

A folder needs `mod.json` to be recognized as a mod at all — the four override files are each optional, include only the ones you need. Folder names starting with `_` (like `_Template`) are reserved and never loaded as mods.

New mods are enabled automatically the first time the game finds them. Use the in-game **Mods** menu (from the main menu) to enable/disable mods and reorder them — when more than one mod changes the same thing, the one lower in the list wins. **Changes apply the next time you restart the game**, not live.

If you subscribe to a mod on the Steam Workshop, it's synced into your local `Mods` folder automatically the next time you launch the game — from that point on it behaves exactly like a mod you installed by hand.

## `mod.json`

```json
{
    "displayName": "My Cool Mod",
    "author": "Your Name",
    "version": "1.0.0",
    "description": "What this mod does.",
    "workshopFileId": ""
}
```

Leave `workshopFileId` blank — it's filled in automatically the first time the mod is published to Steam Workshop, so future publishes update the same item instead of creating a duplicate.

## `unit_overrides.json` — unit stats

A list of entries, each keyed by `unitName`. Include only the fields you want to change; everything else on that unit stays as-is. Every value is written as a **string**, even numbers and true/false.

```json
{
    "overrides": [
        {
            "unitName": "PeasantBowmen",
            "meleeAttack": "8",
            "armor": "10",
            "terrifying": "true"
        }
    ]
}
```

`unitName` must match an existing unit exactly (case-sensitive) — see [Unit name reference](#unit-name-reference) below for the full list. Overriding a `unitName` that doesn't exist is silently skipped (with a warning in the log) — this format can only change existing units, not add new ones.

Available fields:

| Field | Type | Notes |
|---|---|---|
| `unitType` | enum | `Melee`, `Ranged`, `Hybrid`, `Artillery`, `Structure` |
| `unitSize` | enum | `Infantry`, `Cavalry`, `Monstrous`, `SingleUnit`, `Artillery` |
| `rarityTier` | enum | `Common`, `Uncommon`, `Rare`, `Legendary` |
| `meleeAttack`, `meleeDefense`, `weaponStrength`, `armor`, `chargeBonus`, `chargeImpactDamage`, `chargeCount`, `missileStrength`, `ammunition`, `explosionDamage` | int | |
| `hitPointsPerUnit`, `baseUnitCount` | int | must be positive - a zero or negative value is rejected and the previous value is kept |
| `speed`, `leadership`, `baseRange`, `attackAccuracy`, `attackCooldown`, `rateOfFire`, `explosionRange`, `explosionForce` | float | |
| `none`, `standardShields`, `armorPiercing`, `antiInfantry`, `antiLarge`, `terrifying`, `stalwart`, `outrider`, `swampCreature`, `forestDweller`, `chickenFlight`, `ethereal`, `bloodFrenzy`, `rage`, `emblazing`, `unstoppable`, `heavyShields`, `throwingAxes`, `armorSundering`, `monsterSlayer`, `forgefuryTempering`, `flamingAmmo`, `dragonsHoard`, `backStabbers`, `thickScales` | bool | write `"true"` or `"false"` |

### Unit name reference

All 114 unit names, grouped by faction in recruit order (common units first, legendary/monster units last). Also used for `signatureUnit` and `startingArmyUnits` in `hero_overrides.json`, and the `UnitName` condition in `hero_bonus_rules.json`.

**Iron Legion**: `PeasantBowmen`, `LevySwordsmen`, `FieldPikemen`, `LandsknechtGreatswords`, `Arbalesters`, `MilanesePolearms`, `ImperialTemplars`, `DeepwoodRangers`, `BlackEagleHalberdiers`, `BorderlandRiders`, `HearthboundKnights`, `RoyalCavaliers`, `EisenmannRegiment`, `Ashguard`, `KaiserCannon`

**Gruntkin**: `GoblinRabble`, `GoblinScrapShooters`, `DireWolves`, `OrcRavagers`, `OrcImpalers`, `OrcStalkers`, `BogmawTroll`, `ArmoredDirewolves`, `StonehewerGiant`, `StonegulletEnforcers`, `FleshshredderFanatics`, `Direriders`, `Gobbopult`, `Meatgrinders`, `Siegeclaws`

**Raven Host**: `ThrallLevy`, `DriftwoodSkirmishers`, `SeawindSpears`, `Huskarls`, `Shieldmaidens`, `SkogarmadrArchers`, `Berserkers`, `Valkyries`, `VarangianGuard`, `SonsOfFenrir`, `Jomsvikings`, `AngelsOfDeath`, `DraugrBoltThrowers`

**Taelindor Forest**: `SylvanArchers`, `ForestSpirits`, `AshwoodMilitia`, `AerindelGuard`, `Duskspears`, `MistweaverScouts`, `StarStriders`, `Veilpiercers`, `Treants`, `ElarionSentinels`, `SunspireBladelords`, `VeilkinDrakes`, `LorandelStarhurler`, `EmeraldAncient`

**Sanguine Court**: `UndeadLevies`, `BoneclatterSpears`, `FeralHounds`, `GravestoneImps`, `DeathhavenFiends`, `Nightriders`, `BoneshardArchers`, `CorpseClaws`, `MistWraiths`, `BlackWardens`, `Bloodsworn`, `BloodswornKnights`, `Shadelords`, `NecroticChimerae`

**Sakura Dynasty**: `AshigaruSpearmen`, `RoninWanderers`, `DaikyuCommoners`, `FootSamurai`, `NaginataOnna`, `KunoichiInfiltrators`, `DragonTachi`, `EmperorsArquebusiers`, `Hokoshu`, `KitsuneBlademasters`, `Oni`, `BanryuBombardiers`, `JoseonHwacha`, `GoldenSaru`

**Deepstone Hold**: `RiftpickLaborers`, `CrackshotCrossbows`, `Cragflayers`, `HelmwallDefenders`, `DrakefireRiflers`, `GrimfireGuns`, `ThunderhoofChargers`, `GrimazulAncients`, `GlyphstonePhalanx`, `StormForgedBattery`, `TheBulwark`, `AbyssalDelveknights`, `ForgewrathHammers`

**Drakosaur Brood**: `KoboldBrawlers`, `ScalebowKobolds`, `DireRaptors`, `VenomtailArchers`, `Brutes`, `Redhorns`, `RaptorRiders`, `TriceraPlatform`, `BlackDragon`, `Leviathans`, `StegoplateGuard`, `BloodCarnos`, `Kaiju`, `ObsidianScales`

**Special** (garrison structures, not recruitable): `ArchersOfApollo`, `Gate`

## `race_overrides.json` — faction colors

A list of entries, each keyed by `race`. Unlike unit overrides, **all three colors must be specified together** — there's no way to change just one and leave the others alone, since colors don't have a natural "not specified" value in this format.

```json
{
    "overrides": [
        {
            "race": "IronLegion",
            "primaryColor": { "r": 0.1, "g": 0.2, "b": 0.8, "a": 1.0 },
            "secondaryColor": { "r": 0.9, "g": 0.9, "b": 0.9, "a": 1.0 },
            "accentColor": { "r": 1.0, "g": 0.85, "b": 0.0, "a": 1.0 }
        }
    ]
}
```

`race` must be one of: `IronLegion`, `Gruntkin`, `RavenHost`, `TaelindorForest`, `SanguineCourt`, `SakuraDynasty`, `DeepstoneHold`, `DrakosaurBrood`. Color channels are 0-1 floats, not 0-255.

Only colors can be overridden this way — a race's base model/prefab and map region can't be changed through this file.

## `hero_overrides.json` — hero roster data

A list of entries, each keyed by `heroID` (1-16). Same sparse pattern as unit overrides - include only what you want to change.

```json
{
    "overrides": [
        {
            "heroID": "1",
            "startingGold": "20",
            "startingArmyUnits": ["LevySwordsmen", "LevySwordsmen", "PeasantBowmen"]
        }
    ]
}
```

Available fields:

| Field | Type | Notes |
|---|---|---|
| `heroName`, `heroDescription`, `heroPrefabName` | string | these are localization keys, not display text directly |
| `heroBonusDescription` | string array | |
| `unlockCondition`, `demoUnlockCondition` | enum | `None`, `NotAvailableInDemo`, `DiscordExclusive`, `NewsletterExclusive`, `HeroCompletion` |
| `startingGold` | int | |
| `signatureUnit` | enum (`UnitName`) | must be an existing unit |
| `startingArmyUnits` | array of `UnitName` | any entry that isn't a recognized unit name is skipped, the rest still apply |

`heroID` and the hero's `race` cannot be changed — `heroID` is the lookup key, and each hero is permanently tied to their race for campaign generation.

## `hero_bonus_rules.json` — hero and faction battle bonuses

This is the most powerful and most complex file. It replaces the numeric bonuses each hero grants in battle (their passive ability), and the one implemented faction-wide passive (Sakura Dynasty's "all-same-race army" bonus).

**Important: unlike the other three files, a rule list is not merged field-by-field.** If your file includes *any* `statRules` entries for a given `heroID`, they **replace that hero's entire stat-rule set** — not just add to it. Same for `attributeRules` (per hero) and `factionRules` (per race). If you want to tweak one of a hero's bonuses without losing their others, include all of that hero's rules in your file, with your changes applied.

```json
{
    "statRules": [
        { "heroID": "1", "localizationKey": "heroBonusTitle2", "condition": { "filterKind": "Unconditional" }, "stat": "ChargeBonus", "magnitudeKind": "Flat", "value": "5" },
        { "heroID": "1", "localizationKey": "heroBonusTitle1", "condition": { "filterKind": "RarityTier", "requiredRarityTier": "Rare" }, "stat": "MeleeAttack", "magnitudeKind": "Flat", "value": "4" },
        { "heroID": "1", "localizationKey": "heroBonusTitle1", "condition": { "filterKind": "RarityTier", "requiredRarityTier": "Rare" }, "stat": "Leadership", "magnitudeKind": "Flat", "value": "10" }
    ],
    "attributeRules": [
        { "heroID": "4", "localizationKey": "heroBonusTitle7", "condition": { "filterKind": "UnitName", "unitNames": ["OrcRavagers"] }, "grantedAttribute": "Terrifying" }
    ],
    "factionRules": [
        { "race": "SakuraDynasty", "localizationKey": "SakuraDynastyBonusDescription", "stat": "MeleeAttack", "magnitudeKind": "Flat", "value": "4" },
        { "race": "SakuraDynasty", "localizationKey": "SakuraDynastyBonusDescription", "stat": "Leadership", "magnitudeKind": "Flat", "value": "20" }
    ]
}
```

### `statRules` entry fields

| Field | Type | Notes |
|---|---|---|
| `heroID` | int | which hero grants this bonus |
| `localizationKey` | string | the localization key used to display the bonus's name in the UI |
| `condition` | object | see Conditions below |
| `stat` | enum (`UnitStat`) | `MeleeAttack`, `MeleeDefense`, `WeaponStrength`, `Accuracy`, `Range`, `MissileStrength`, `Speed`, `Armor`, `ChargeBonus`, `Leadership`, `Ammunition`, `ChargeImpactDamage` |
| `magnitudeKind` | enum | `Flat` (add `value` directly) or `PercentOfCurrentValue` (add `value` × the stat's current value - e.g. `0.5` means +50%) |
| `value` | float | |

### `attributeRules` entry fields

Same as `statRules` except instead of `stat`/`magnitudeKind`/`value`, there's a single `grantedAttribute` (enum) — the hero grants this attribute to matching units if they don't already have it. Valid values: `StandardShields`, `ArmorPiercing`, `AntiInfantry`, `AntiLarge`, `Terrifying`, `Stalwart`, `Outrider`, `SwampCreature`, `ForestDweller`, `ChickenFlight`, `Ethereal`, `BloodFrenzy`, `Rage`, `Emblazing`, `Unstoppable`, `HeavyShields`, `ThrowingAxes`, `ArmorSundering`, `MonsterSlayer`, `ForgefuryTempering`, `FlamingAmmo`, `DragonsHoard`, `BackStabbers`, `ThickScales`.

### `factionRules` entry fields

Same shape as `statRules`, but keyed by `race` instead of `heroID`, and with no `condition` (a faction bonus applies to every unit once its army-composition requirement is met - today that's only "army is entirely one race," and only wired up for Sakura Dynasty).

### Conditions

Every `condition` object has a `filterKind`, and depending on which one, one or two additional fields:

| `filterKind` | Additional fields | Meaning |
|---|---|---|
| `Unconditional` | none | applies to every unit |
| `RarityTier` | `requiredRarityTier`: `Common`/`Uncommon`/`Rare`/`Legendary` | applies only to units of that rarity |
| `UnitName` | `unitNames`: array of `UnitName` | applies only to the listed units |
| `UnitTag` | `tag`: string | applies to units matching a named tag - currently `"Goblin"` or `"MeleeInfantry"` |
| `UnitType` | `unitTypes`: array of `UnitType` | applies to units of the listed type(s) |
| `UnitSize` | `unitSizes`: array of `UnitSize` | applies to units of the listed size(s) |
| `EnemyRace` | `requiredEnemyRace`: a `Race` | applies only when fighting that race |

## Testing your mod

1. Put your mod folder in `Mods/` as described above.
2. Launch the game (or restart it if it was already running).
3. Check the in-game **Mods** menu to confirm it's listed and enabled.
4. Play a battle and confirm the change - the game logs a line for every override file it applies (and warns about anything it couldn't parse) if you need to debug something that isn't working as expected.

If a file has a typo or invalid value, the game skips just that field (or that file, if the whole thing fails to parse) and logs a warning rather than crashing - check the log if something doesn't seem to be applying.
