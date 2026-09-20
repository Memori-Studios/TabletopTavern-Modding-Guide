# Tabletop Tavern Modding Guide

Tabletop Tavern supports mods that override unit stats, faction colors, hero data, hero/faction battle bonuses, gear effect magnitudes, shop/economy pricing, enemy army/garrison generation, race passive tuning, weather effects and odds, and localized text — no code required, just plain text files. This guide covers the file formats. See the [`ExampleMod/`](ExampleMod/) folder for a complete, working example you can copy and edit.

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
        gear_overrides.json   <- optional
        army_generation_rules.json <- optional
        economy_overrides.json <- optional
        race_bonus_overrides.json <- optional
        weather_overrides.json <- optional
        localization_overrides.json <- optional
```

A folder needs `mod.json` to be recognized as a mod at all — the ten override files are each optional, include only the ones you need. Folder names starting with `_` (like `_Template`) are reserved and never loaded as mods.

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

The stock values for every unit are in [`unit_stats.csv`](unit_stats.csv) - one row per unit, one column per field below, in the same spelling `unit_overrides.json` uses. Open it in a spreadsheet to see what you are changing from.

Available fields:

| Field | Type | Notes |
|---|---|---|
| `unitType` | enum | `Melee`, `Ranged`, `Hybrid`, `Artillery`, `Structure`. `Hybrid` units both shoot and hold the melee line: they deploy in the front row, don't kite, gain melee prestige stats and melee gear, and fight with their melee stats in auto-resolved battles - but they still carry a bow or throwing weapon and fire at range. They receive no ammunition bonuses of any kind, so give them a small `ammunition` pool. The stock hybrids are `Berserkers`, `Cragflayers` and `KunoichiInfiltrators`. |
| `unitSize` | enum | `Infantry`, `Cavalry`, `Monstrous`, `SingleUnit`, `Artillery` |
| `rarityTier` | enum | `Common`, `Uncommon`, `Rare`, `Legendary` |
| `race` | enum | `IronLegion`, `Gruntkin`, `RavenHost`, `TaelindorForest`, `SanguineCourt`, `SakuraDynasty`, `DeepstoneHold`, `DrakosaurBrood`, `Special` - moves the unit to that faction's collection/army-builder roster. Doesn't change the unit's model, icon, or portrait, which stay whatever they were originally. |
| `meleeAttack` | int | Melee skill. Chance to land a swing is `35 + (attacker meleeAttack - defender meleeDefense) x 2` percent, clamped to 10-90. |
| `meleeDefense` | int | The defending half of that same formula. A unit hit from the flank defends at half this value. |
| `weaponStrength` | int | Damage of each melee hit that lands, before the target's armor. There is no damage roll, so doubling it doubles melee damage. |
| `armor` | int | Cuts every hit taken by `armor / (armor + 100)`: 100 armor halves damage, 50 armor cuts it by a third. Armor-piercing attackers only get half that reduction. |
| `hitPointsPerUnit` | int | Health of one model. Squad health is this times `baseUnitCount`. Must be positive - zero or negative is rejected and the previous value kept. |
| `baseUnitCount` | int | Models in the squad at full strength. Must be positive - zero or negative is rejected and the previous value kept. |
| `speed` | float | Movement speed. The in-world value is this divided by 10, so 30 is a slow footsoldier and 80 is cavalry. |
| `leadership` | float | Maximum morale, 0-100. Morale drains under fire and the squad breaks for good when it reaches 5, so more leadership means more punishment before it runs. Each prestige level adds 5. |
| `attackCooldown` | float | Seconds between melee swings for every unit, shooters included (they swing with it once caught in melee). Lower is faster. |
| `chargeBonus` | int | Added to both `meleeAttack` and `weaponStrength` on impact after a charge has built up for 2 seconds. Fades 6 seconds after contact, and is cancelled outright by anti-large defenders, garrison gates, forest, swamp and rain. |
| `chargeImpactDamage` | int | Damage dealt to each enemy model knocked over by the charge. Knockback only happens on a charge into a target that is not bracing: a large unit hitting a small one always knocks back, small on small has a 15% chance per model, and small on large never does. |
| `chargeCount` | int | Charges the squad can make in one battle. At zero it is Exhausted and no longer gets `chargeBonus`. |
| `baseRange` | float | Reach of ranged and artillery attacks in world units. Also the cast range for mages. Ignored on pure melee units. |
| `attackAccuracy` | float | Percent chance, 0-100, that a shot is aimed at its target rather than fired into the ground. Fire-at-Will shooting takes a flat 20-point penalty unless the unit has `steadyAim`. |
| `missileStrength` | int | Damage of each ranged hit that lands, before the target's armor. Arrows, bolts, bullets and the direct hit of a shell. |
| `rateOfFire` | float | Seconds between shots for `Artillery` and `Structure` units only, and seconds between casts for mages. Regular `Ranged` and `Hybrid` shooters ignore it and reload on a fixed 5 seconds (4 with `shotDiscipline`). This is the ranged counterpart of `attackCooldown`, which is the melee swing interval. |
| `ammunition` | int | Shots the squad can fire before it stops shooting. Charges for mages. Garrison gate archers ignore it. |
| `explosionDamage` | int | `Artillery` only. Damage dealt to every model inside `explosionRange` when a shell lands. |
| `explosionRange` | float | `Artillery` only. Radius of the blast in world units. |
| `explosionForce` | float | `Artillery` only. How hard the blast throws the models it catches. Higher values send them further. |
| `none`, `standardShields`, `armorPiercing`, `antiInfantry`, `antiLarge`, `terrifying`, `stalwart`, `outrider`, `swampCreature`, `forestDweller`, `chickenFlight`, `ethereal`, `bloodFrenzy`, `rage`, `emblazing`, `unstoppable`, `heavyShields`, `throwingAxes`, `armorSundering`, `monsterSlayer`, `forgefuryTempering`, `flamingAmmo`, `dragonsHoard`, `backStabbers`, `thickScales` | bool | write `"true"` or `"false"` |
| `shotDiscipline`, `overdraw`, `steadyAim`, `demolisher`, `powderReserves`, `deepQuivers` | bool | shooter traits - `shotDiscipline` (20% faster reload) and `overdraw` (+15% range) need a unit that shoots; `steadyAim` (no Fire-at-Will accuracy penalty) does something on `Ranged` and `Hybrid`, but not `Artillery`, which has no fire mode to switch; `demolisher` (+30% explosion damage and radius) and `powderReserves` (+50% ammunition) only do anything on `Artillery`; `deepQuivers` (+500 ammunition) only does anything on `Ranged` - it is ignored on `Hybrid`, whose ammo pool is a token handful of throwing weapons |

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
| `heroName`, `heroDescription` | string | localization keys, not display text directly |
| `heroPrefabName` | string | also a localization key, despite the name - it's the key for the hero's lore paragraph |
| `heroBonusDescription` | string array | localization keys, **exactly two entries** - see below |
| `unlockCondition`, `demoUnlockCondition` | enum | `None`, `NotAvailableInDemo`, `DiscordExclusive`, `NewsletterExclusive`, `HeroCompletion` |
| `startingGold` | int | |
| `signatureUnit` | enum (`UnitName`) | must be an existing unit |
| `startingArmyUnits` | array of `UnitName` | any entry that isn't a recognized unit name is skipped, the rest still apply |

`heroID` and the hero's `race` cannot be changed — `heroID` is the lookup key, and each hero is permanently tied to their race for campaign generation.

### Changing a hero's text

Because these fields are keys rather than text, there are two different ways to change what a player reads, and you usually want the first:

- **To reword an existing hero**, leave `hero_overrides.json` alone entirely and override the *text behind the key* in [`localization_overrides.json`](#localization_overridesjson--text-and-translations). Look up the hero's current key (the exported template in `_Template/` lists it) and give that key your new text.
- **To point a hero at a brand-new key of your own**, set the field here *and* define that key in `localization_overrides.json`. These two always go together: a key with no text behind it displays as the raw key itself and logs an error every time the panel draws.

`heroBonusDescription` has one extra rule, and it's the single most common thing modders get wrong - see [Bonus text comes in pairs](#bonus-text-comes-in-pairs) for the symptom.

The game shows each bonus as `Name: description`, but a hero only stores the *description* key - the **name key is derived from it** by swapping `heroBonusDescription` for `heroBonusTitle` inside the key. So `heroBonusDescription1` implies `heroBonusTitle1`, and the two are always a matched pair:

| Key | Holds | Example |
|---|---|---|
| `heroBonusTitle3` | the short **name** only | `Ranger Captain` |
| `heroBonusDescription3` | the **effect text** only | `Deepwood Rangers gain +10 [Accuracy] and +4 [Missile Strength]` |

Two consequences worth spelling out:

- **If you override one, override the other.** Putting the whole sentence into the title key leaves the untouched description key appended after it, so the panel reads `Your new sentence: the original effect text`.
- **If you invent a key** that doesn't contain the text `heroBonusDescription`, there's no name to derive and the bonus renders as the description alone, with no name prefix. To get a custom name too, follow the convention: name your keys something like `myModHeroBonusDescriptionA` and `myModHeroBonusTitleA`, and define both.

The array must have exactly two entries, both non-empty. Anything else is rejected with a warning and the hero keeps their original bonus keys.

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
| `localizationKey` | string | the localization key for the bonus's **name**. Keep the text behind it short - it's shown as a label beside the stat number on unit tooltips, so a full sentence reads badly there. Note this is the `heroBonusTitleN` half of a pair; changing what it says does **not** update the hero's effect line, which is the `heroBonusDescriptionN` half. See [Bonus text comes in pairs](#bonus-text-comes-in-pairs). |
| `condition` | object | see Conditions below |
| `stat` | enum (`UnitStat`) | `MeleeAttack`, `MeleeDefense`, `WeaponStrength`, `Accuracy`, `Range`, `MissileStrength`, `Speed`, `Armor`, `ChargeBonus`, `Leadership`, `Ammunition`, `ChargeImpactDamage` |
| `magnitudeKind` | enum | `Flat` (add `value` directly) or `PercentOfCurrentValue` (add `value` × the stat's current value - e.g. `0.5` means +50%) |
| `value` | float | |

### `attributeRules` entry fields

Same as `statRules` except instead of `stat`/`magnitudeKind`/`value`, there's a single `grantedAttribute` (enum) — the hero grants this attribute to matching units if they don't already have it. Valid values: `StandardShields`, `ArmorPiercing`, `AntiInfantry`, `AntiLarge`, `Terrifying`, `Stalwart`, `Outrider`, `SwampCreature`, `ForestDweller`, `ChickenFlight`, `Ethereal`, `BloodFrenzy`, `Rage`, `Emblazing`, `Unstoppable`, `HeavyShields`, `ThrowingAxes`, `ArmorSundering`, `MonsterSlayer`, `ForgefuryTempering`, `FlamingAmmo`, `DragonsHoard`, `BackStabbers`, `ThickScales`.

### `factionRules` entry fields

Same shape as `statRules`, but keyed by `race` instead of `heroID`, and with no `condition` (a faction bonus applies to every unit once its army-composition requirement is met - today that's only "army is entirely one race," and only wired up for Sakura Dynasty).

Note: only `magnitudeKind: "Flat"` is meaningful here. Unlike hero stat rules, the faction path has no current-stat value to scale against, so `PercentOfCurrentValue` is ignored - the raw `value` is added as a flat amount instead (logged as a warning). Author faction bonuses as flat values.

### Conditions

Every `condition` object has a `filterKind`, and depending on which one, one or two additional fields:

| `filterKind` | Additional fields | Meaning |
|---|---|---|
| `Unconditional` | none | applies to every unit |
| `RarityTier` | `requiredRarityTier`: `Common`/`Uncommon`/`Rare`/`Legendary` | applies only to units of that rarity |
| `UnitName` | `unitNames`: array of `UnitName` | applies only to the listed units |
| `UnitTag` | `tag`: string | applies to units matching a named tag - currently `"Goblin"` or `"MeleeInfantry"` (which covers `Hybrid` units as well as `Melee` ones) |
| `UnitType` | `unitTypes`: array of `UnitType` | applies to units of the listed type(s) |
| `UnitSize` | `unitSizes`: array of `UnitSize` | applies to units of the listed size(s) |
| `EnemyRace` | `requiredEnemyRace`: a `Race` | applies only when fighting that race |

## `gear_overrides.json` — gear effect magnitudes

A list of entries, each keyed by `gearID`. There's only one overridable field: `gearModifierValue`, the number each gear's effect is built around - Arming Swords' bonus [Melee Attack], Longbows' bonus [Range], Common Builder's gold discount, and so on. This is the same value shown in that gear's in-game tooltip, so overriding it updates both the tooltip and the actual effect together.

```json
{
    "overrides": [
        { "gearID": "ArmingSwords", "gearModifierValue": "10" },
        { "gearID": "Longbows", "gearModifierValue": "35" }
    ]
}
```

Gear whose effect is a flat unlock rather than a magnitude (e.g. Diamond Tipped Arrows granting [Armor Piercing], Iron Bank's doubled interest) has no meaningful modifier value - overriding one of those does nothing, since nothing reads it. `gearID` must be one of:

`ArmingSwords`, `BucklerShields`, `Longbows`, `Glaives`, `ConscriptionOrders`, `TexanBBQ`, `JoustingLances`, `GnomishArmorers`, `DiamondTippedArrows`, `WellHonedAxes`, `RingoftheElvenKing`, `RavensEye`, `BallisticCharts`, `Turkey`, `HeavyWeapons`, `Shungite`, `QuantitativeEasingPolicy`, `TowerShields`, `IronBank`, `OmenofFamine`, `OrnateRing`, `ThePotato`, `Cauldron`, `DwarvenTaxCollectors`, `CommonBuilder`, `UncommonBuilder`, `RareBuilder`, `PrivateeringPapers`, `CookieAndFowlCard`, `BraceletoftheSunGoddess`, `BearSpray`, `LuckyHorseshoe`, `RiverTrout`, `MichaelsSecretStuff`, `Mitre`, `ChugJug`, `PumpkinPie`, `AuraFarming`, `NorthernLooters`, `JailersKey`

Only the modifier value can be overridden this way - a gear's name, rarity, and shop-ban status can't be changed through this file.

## `army_generation_rules.json` — enemy army and garrison generation

**This file works differently from the others above.** Unit stats, gear, etc. are flat data you patch field-by-field. Enemy army composition is a branching decision (which board/act, whether it's the final battle, how many battles you've fought, difficulty) so this file is a **list of rules, matched top-to-bottom** - the first rule whose conditions all match wins. Your rules are checked before the game's built-in ones, so to change one specific situation, write one specific rule for it; anything you don't cover falls through to the default game balance untouched. Leaving a field out of a rule makes it match regardless of that field's value.

**Be as specific as you can.** A rule with fewer fields set matches *more* situations - e.g. a rule with only `"board": 1` set (no `finalBattle`, no battle-count range) would shadow every single board-1 case, final battles included. The exported template below is fully specific (one rule per exact situation) - copy the row(s) you want to change from it rather than writing rules from scratch.

```json
{
    "enemyArmyRules": [
        {
            "board": 1,
            "finalBattle": false,
            "battlesFoughtMin": 7,
            "tierCounts": [ { "tier": 1, "count": 3 }, { "tier": 2, "count": 2 }, { "tier": 3, "count": 2 } ]
        }
    ],
    "townGarrisonRules": [
        {
            "townSize": "City",
            "bookNumber": 1,
            "difficultyImperator": false,
            "tierCounts": [ { "tier": 1, "count": 2 }, { "tier": 2, "count": 2 }, { "tier": 3, "count": 2 } ]
        }
    ],
    "enemyPrestigeRules": [
        { "actNumber": 2, "enhanced": true, "chancePerSquad": "0.35", "maxPrestigedSquads": "3", "prestigeTwoChance": "0.20" }
    ]
}
```

All three arrays are independent and optional - a mod can supply just one.

### `enemyArmyRules` entry fields

| Field | Type | Notes |
|---|---|---|
| `board` | int | required - which campaign board/act |
| `finalBattle` | bool | required |
| `knightDifficulty` | bool | optional - omit to match either difficulty. Only meaningful for final battles; the base game ignores it for regular battles |
| `battlesFoughtMin` | int | optional - inclusive lower bound |
| `battlesFoughtMax` | int | optional - exclusive upper bound. Only meaningful for regular (non-final) battles; the base game ignores battle count for final battles |
| `tierCounts` | array of `{tier, count}` | required - how many squads to draft from each unit rarity tier (1=Common, 2=Uncommon, 3=Rare, 4=Legendary) |

### `townGarrisonRules` entry fields

| Field | Type | Notes |
|---|---|---|
| `townSize` | enum | required - `Village`, `Castle`, `City` |
| `bookNumber` | int | required |
| `difficultyImperator` | bool | optional - omit to match either difficulty |
| `tierCounts` | array of `{tier, count}` | required, same shape as above |

### `enemyPrestigeRules` entry fields

Controls the odds that a generated enemy squad spawns already prestiged (Duke difficulty and above). No conditions here beyond act and difficulty - every field is required.

| Field | Type | Notes |
|---|---|---|
| `actNumber` | int | required |
| `enhanced` | bool | required - `true` for Emperor+ difficulty's rates, `false` for Duke/Baron |
| `chancePerSquad` | float | chance (0-1) each squad spawns prestiged |
| `maxPrestigedSquads` | int | cap on prestiged squads per army |
| `prestigeTwoChance` | float | chance (0-1) a prestiged squad is prestige 2 instead of 1 |

If no rule (yours or the game's default) matches a given board/act at all, it falls back gracefully: `enemyArmyRules`/`townGarrisonRules` produce an empty army/garrison for that case (with a warning in the log - this is the same as an unmodded game asking for a board that doesn't exist), while `enemyPrestigeRules` clamps to the nearest of the base game's 3 acts rather than disabling prestige entirely. This means you can add rules for a new board 4+ without needing to also define prestige rules for it.

## `economy_overrides.json` — shop and economy values

Covers gold costs and odds across the game: unit and town recruit costs, gear and consumable shop prices, card pack prices, consumable drop odds, town bounty gold, bank interest, and battle/event gold rewards. **All nine sections below are independent and optional** — a mod can supply just the ones it needs, same as `army_generation_rules.json`.

```json
{
    "unitTierCosts": [
        { "tier": "4", "cost": "80" }
    ],
    "townRecruitCosts": [
        { "townSize": "City", "cost": "30" }
    ],
    "gearRarityCosts": [
        { "gearRarity": "Rare", "cost": "10" }
    ],
    "consumableRarityCosts": [
        { "consumableRarity": "Legendary", "cost": "45" }
    ],
    "cardPackPrices": [
        { "packID": "1", "price": "8" }
    ],
    "consumableDropOdds": [
        { "actNumber": "1", "consumable": "LambSauce", "weight": "5" }
    ],
    "townBountyRanges": [
        { "townSize": "Village", "min": "6", "max": "10" }
    ],
    "bank": { "maxInterest": "8" },
    "battleRewards": { "hordeReward": "10" }
}
```

### `unitTierCosts` — recruiting units by rarity tier

| Field | Type | Notes |
|---|---|---|
| `tier` | int | 1-4, same tier numbering as `tierCounts` above (1=Common, 2=Uncommon, 3=Rare, 4=Legendary) |
| `cost` | int | gold cost to recruit a unit of that tier |

### `townRecruitCosts` — recruiting garrison units from a town

| Field | Type | Notes |
|---|---|---|
| `townSize` | enum | `Village`, `Castle`, `City` - same values as `townGarrisonRules` above |
| `cost` | int | |

### `gearRarityCosts` — buying gear in the shop

| Field | Type | Notes |
|---|---|---|
| `gearRarity` | enum | `Common`, `Uncommon`, `Rare` only - gear has no Legendary rarity, unlike consumables |
| `cost` | int | |

### `consumableRarityCosts` — buying potions/consumables in the shop

| Field | Type | Notes |
|---|---|---|
| `consumableRarity` | enum | `Common`, `Uncommon`, `Rare`, `Legendary` |
| `cost` | int | |

### `cardPackPrices` — buying card packs

| Field | Type | Notes |
|---|---|---|
| `packID` | int | `0`=Gear Pack, `1`=Card Pack 1, `2`=Card Pack 2, `3`=Card Pack 3, `4`=Card Pack 4 |
| `price` | int | |

### `consumableDropOdds` — shop/reward consumable odds

Each entry is a relative weight (not a percentage) for how likely that consumable is to appear, out of all consumables available that act - higher means more common. Weights only need to be set relative to each other, so you don't need to rebalance every entry to change one item's rarity.

| Field | Type | Notes |
|---|---|---|
| `actNumber` | int | 1-3 |
| `consumable` | enum (`ConsumableEnum`) | `MinorHealth`, `MajorHealth`, `Prestige`, `Duplicate`, `NewUnit`, `Alchemist`, `Rewind`, `TrialofGrasses`, `FateshineElixir`, `RunewellNectar`, `LambSauce`, `ManaDraught` (Spell Update builds only; ignored before then) |
| `weight` | float | |

### `townBountyRanges` — gold looted from towns

Unlike the sparse fields elsewhere in this file, **both `min` and `max` must be given together** - a range needs both ends to mean anything. `max` must be greater than or equal to `min`, or the entry is rejected (logged as a warning) rather than applied, since an invalid range would crash the game the next time that town size is generated.

| Field | Type | Notes |
|---|---|---|
| `townSize` | enum | `Village`, `Castle`, `City` |
| `min` | int | inclusive |
| `max` | int | exclusive |

### `bank` — turn-end interest

A single object, not a list. Both fields optional independently.

| Field | Type | Notes |
|---|---|---|
| `maxInterest` | int | cap on gold earned per turn from interest, before gear bonuses (Dwarven Tax Collectors, Iron Bank, etc.) are applied on top |
| `potionRewardsOdds` | int | percent chance (0-100) of a bonus consumable after a battle |

### `battleRewards` — post-battle gold

A single object, not a list. Each field optional independently.

| Field | Type | Notes |
|---|---|---|
| `ransomCaptivesReward` | int | gold per captive ransomed |
| `skirmishReward` | int | base gold for winning a Skirmish engagement |
| `hordeReward` | int | base gold for winning a Horde engagement |

## `localization_overrides.json` — text and translations

Replaces the display text behind any localization key, per language. This is what lets you rename or re-translate anything the game shows as text — including the **bonus names** referenced by `localizationKey` in `hero_bonus_rules.json`, the hero name/description/lore keys from `hero_overrides.json`, and any other UI, event or lore string.

A flat list of entries, each with a `locale`, a `key`, and the `text` to show. (It's a flat list rather than nested by language because of how the game parses these files.)

```json
{
    "overrides": [
        { "locale": "en", "key": "heroBonusTitle2", "text": "Inspiring Presence" },
        { "locale": "en", "key": "heroBonusDescription2", "text": "All units gain +2 [Charge Bonus]" },
        { "locale": "en", "key": "exampleCustomBonusName", "text": "Example Custom Bonus" }
    ]
}
```

| Field | Type | Notes |
|---|---|---|
| `locale` | string | language code the text applies to. One entry per language you want to cover — see the list below. |
| `key` | string | the localization key to replace. Can be an existing key (to rename/retranslate something the game already shows) or a brand-new key of your own. |
| `text` | string | the text to display. |

Supported locale codes: `en` (English), `de` (German), `es` (Spanish), `fr` (French), `ja` (Japanese), `ko` (Korean), `ru` (Russian), `zh` (Simplified Chinese), `zh-Hant` (Traditional Chinese). The code must match exactly.

**Overriding an existing key** changes that text everywhere it appears in-game. For example, `heroBonusTitle2` is the name of Edric Valeward's charge bonus and `heroBonusDescription2` is what that bonus does, so the two entries above rewrite his second bonus wherever it's shown. Those two go together - see [Bonus text comes in pairs](#bonus-text-comes-in-pairs) below.

**Inventing a new key** is what makes custom bonuses possible. `hero_bonus_rules.json` requires a `localizationKey` for every rule, and normally you'd have to reuse an existing hero's bonus name. Instead, point a rule at your own key (e.g. `"localizationKey": "exampleCustomBonusName"`) and define that key here — now your bonus displays its own name. Keep it to a short name: on unit tooltips the game prints this text as a label next to the stat number it's already drawing, so the name alone is what you want there.

### Bonus text comes in pairs

**A hero's bonus is two keys, and rebalancing usually means editing both.** This is the most common mod bug, and it looks like text that's only half-replaced.

| Key | Holds | Vanilla example |
|---|---|---|
| `heroBonusTitle3` | the short **name** | `Ranger Captain` |
| `heroBonusDescription3` | the **effect text** | `Deepwood Rangers gain +10 [Accuracy] and +4 [Missile Strength]` |

The Hero Effects panel renders them joined as `Name: description`. `hero_bonus_rules.json` only ever refers to the **title** key, so it's easy to assume that's the whole thing - but if you override just the title with a full sentence, the untouched description is still appended after it:

```text
No Mere Ranger: All [Ranged] units gain +4 [Missile Strength] and [Armor Piercing]: Deepwood Rangers gain +10 [Accuracy] and +4 [Missile Strength]
                                                                                  ^ the vanilla description you didn't override
```

Override both instead:

```json
{ "locale": "en", "key": "heroBonusTitle3",       "text": "No Mere Ranger" },
{ "locale": "en", "key": "heroBonusDescription3", "text": "All [Ranged] units gain +4 [Missile Strength]; [Common] and [Uncommon] units gain [Armor Piercing]" }
```

**Descriptions do not update themselves.** The numbers in a description are hand-written text, not generated from your rules. Change a value in `hero_bonus_rules.json` and the effect line keeps advertising the old one until you override the matching `heroBonusDescriptionN` to match. (The per-unit stat tooltips are the exception - those read the live rule value and pair it with your `localizationKey` name, which is why keeping that name short matters.)

**Which number goes with which hero?** The keys run in order, two per hero: hero 1 uses `heroBonusTitle1`/`Description1` and `heroBonusTitle2`/`Description2`, hero 2 uses `3` and `4`, and so on. The exported `_Template/` files list each hero's current keys.

**Writing a description.** Wrap stat and attribute names in square brackets and the game colours them: `[Melee Attack]`, `[Missile Strength]`, `[Armor Piercing]`, `[Stalwart]`, `[Rare]`, `[Common]`. The bracketed text has to match the game's own display name for that stat or attribute, so copy the spelling from a vanilla description. `+N` values are coloured automatically. A bracket the game doesn't recognise is left as literal text, which is the quickest way to spot a typo.

A hero's `heroName` / `heroDescription` / `heroPrefabName` fields are localization keys too - see [Changing a hero's text](#changing-a-heros-text) for how to reword those.

**Language fallback.** If the player's language has no entry for a key, the game falls back to your `en` entry for that same key, and only then to its own built-in text. So a mod that ships English only still shows its text to everyone — a renamed hero keeps the new name in every language rather than reverting to the original. Add entries for other languages to translate on top of that.

Overrides match purely by `key`, independent of which in-game text table asked for it. That covers the main UI table, event text and lore text alike. The flip side: if the same key exists in more than one table, one override entry changes all of them. A key you define but never reference shows up nowhere - it's harmless.

## `race_bonus_overrides.json` — race passive tuning

Every playable race has a unique battlefield passive (Gruntkin's Crashing Horde, Sanguine Court's fearlessness, etc.). This file lets you rebalance the **numbers** of those passives — how big each bonus is, how many times it stacks, how fast it ramps, how long it lasts. It does **not** let you change *how* a passive triggers or invent a new one; the trigger logic stays fixed, you're only tuning its values.

Each race is its own block, and every field inside a block is optional — set only the values you want to change, the rest keep their defaults. Omit a race block entirely to leave that race untouched.

```json
{
    "gruntkin":        { "weaponStrengthPerStack": "8", "maxStacks": "5" },
    "drakosaurBrood":  { "weaponStrengthPerStack": "10" },
    "taelindorForest": { "rangedBonusCap": "30" },
    "sakuraDynasty":   { "meleeAttackPerStage": "6", "maxStages": "4" },
    "deepstoneHold":   { "weaponStrengthPerDeath": "3" },
    "ironLegion":      { "clampDurationSeconds": "15" },
    "ravenHost":       { "meleeAttackBonus": "25", "durationSeconds": "25" },
    "sanguineCourt":   { "immuneToTerror": "false" }
}
```

Timing/threshold fields (`updateInterval`, `secondsPerStage`, `durationSeconds`, `clampDurationSeconds`, `healthThreshold`) must be **greater than zero** — an invalid value is rejected (logged as a warning) and the default is kept. Bonus magnitudes and stack/stage caps may be set to `0` to effectively switch a passive off.

### `gruntkin` — Crashing Horde

Each other living Gruntkin squad above the health threshold grants a stacking WeaponStrength bonus to the whole army.

| Field | Type | Default | Notes |
|---|---|---|---|
| `weaponStrengthPerStack` | int | 5 | WeaponStrength added per qualifying ally |
| `maxStacks` | int | 4 | stack cap (so default max is +20) |
| `healthThreshold` | float | 0.5 | fraction of max HP a squad must exceed to count (0.5 = above 50%) |
| `updateInterval` | float | 1.0 | seconds between re-evaluations |

### `drakosaurBrood` — Pack Instinct

For each other Drakosaur squad attacking the same enemy squad, this squad gains a stacking WeaponStrength bonus.

| Field | Type | Default | Notes |
|---|---|---|---|
| `weaponStrengthPerStack` | int | 8 | WeaponStrength per co-attacking squad |
| `maxStacks` | int | 2 | stack cap (default max +16) |
| `updateInterval` | float | 0.5 | seconds between re-evaluations |

### `taelindorForest` — Hunter's Patience

While a squad holds still, it accrues a bonus each tick up to a cap; ranged squads build Accuracy, melee squads build WeaponStrength. Moving or charging clears the accrued bonus.

| Field | Type | Default | Notes |
|---|---|---|---|
| `rangedBonusPerTick` | int | 3 | Accuracy gained per tick (ranged squads) |
| `meleeBonusPerTick` | int | 2 | WeaponStrength gained per tick (melee squads) |
| `rangedBonusCap` | int | 20 | max accrued Accuracy |
| `meleeBonusCap` | int | 12 | max accrued WeaponStrength |
| `updateInterval` | float | 1.0 | seconds per tick |

### `sakuraDynasty` — Kensei's Eye

Continuous melee combat grants MeleeAttack in stages; leaving combat resets it.

| Field | Type | Default | Notes |
|---|---|---|---|
| `meleeAttackPerStage` | int | 5 | MeleeAttack per stage reached |
| `secondsPerStage` | float | 10.0 | continuous-combat seconds needed per stage |
| `maxStages` | int | 3 | stage cap (default max +15 after 30s) |
| `updateInterval` | float | 1.0 | seconds between checks |

### `deepstoneHold` — Oathcarved

Every unit death in the squad permanently buffs the survivors. Stacks with no cap for the whole battle.

| Field | Type | Default | Notes |
|---|---|---|---|
| `weaponStrengthPerDeath` | int | 2 | permanent WeaponStrength granted to survivors per death |

### `ironLegion` — Iron Resolve

The first time a squad reaches Wavering morale, its morale is held there for a grace period instead of breaking. (The morale level it's pinned to is fixed and not moddable — only the duration is.)

| Field | Type | Default | Notes |
|---|---|---|---|
| `clampDurationSeconds` | float | 10.0 | how long morale is held at Wavering |

### `ravenHost` — Deathcry

When a Raven Host squad falls, surviving same-team Raven Host squads gain a temporary MeleeAttack bonus. A later loss refreshes the timer but doesn't stack the bonus.

| Field | Type | Default | Notes |
|---|---|---|---|
| `meleeAttackBonus` | int | 20 | MeleeAttack granted to survivors |
| `durationSeconds` | float | 20.0 | how long the bonus lasts |

### `sanguineCourt` — fearless immunities

Sanguine Court squads ignore several morale penalties. These are on/off toggles rather than numbers — set one to `false` to remove that immunity.

| Field | Type | Default | Notes |
|---|---|---|---|
| `immuneToFlankMorale` | bool | true | immune to the morale penalty from being flanked |
| `immuneToTerror` | bool | true | immune to terror (fear from terrifying enemies) |
| `immuneToRetreatingAlliesMorale` | bool | true | immune to the morale penalty from nearby allies retreating |

## `weather_overrides.json` - weather effects and odds

Battles roll one of four weathers (Clear Skies, Rain, Fog, Snow). This file lets you rebalance the **numbers** behind each weather's effect and change **how likely** each weather is in each region. It does not add new weathers or change what kind of effect a weather has; Rain always slows large units, Fog always hampers ranged units, Snow always lowers morale.

Every block and field is optional. Omit anything you don't want to change.

```json
{
    "rain": { "largeUnitSpeedModifier": "0.5", "removesChargeBonus": "false", "autoResolveAccuracyModifier": "0.5" },
    "snow": { "moralePenalty": "-15" },
    "fog":  { "accuracyModifier": "0.5", "rangeModifier": "0.75" },
    "regionWeathers": [
        {
            "race": "Gruntkin",
            "weathers": [
                { "weather": "ClearSkies", "likelihood": "40" },
                { "weather": "Rain",       "likelihood": "60" }
            ]
        }
    ]
}
```

Modifiers are the **fraction kept**, not the reduction: `0.5` halves a stat, `0.75` keeps three quarters of it, `1` switches the effect off. The weather tooltips in game show the live percentages, so a modded value is what the player reads.

### `rain`

| Field | Type | Default | Notes |
|---|---|---|---|
| `largeUnitSpeedModifier` | float | 0.5 | speed multiplier for large units while it rains; must be greater than zero |
| `removesChargeBonus` | bool | true | whether large units lose their charge bonus while it rains; `false` lets them charge as normal |
| `autoResolveAccuracyModifier` | float | 0.5 | accuracy multiplier applied to every squad in the auto-resolve prediction while it rains |

### `snow`

| Field | Type | Default | Notes |
|---|---|---|---|
| `moralePenalty` | float | -10 | added to every squad's max and current morale; negative lowers it, positive would raise it |

### `fog`

| Field | Type | Default | Notes |
|---|---|---|---|
| `accuracyModifier` | float | 0.5 | accuracy multiplier for ranged units |
| `rangeModifier` | float | 0.5 | range multiplier for ranged units (also shrinks the garrison gate's range arc) |

### `regionWeathers` - per-region odds

Each campaign region belongs to one race, so a region is keyed by that race's name (the same `race` names used elsewhere in this guide: `IronLegion`, `Gruntkin`, `RavenHost`, `TaelindorForest`, `SanguineCourt`, `SakuraDynasty`, `DeepstoneHold`, `DrakosaurBrood`).

An entry **replaces that region's whole weather table**, so list every weather you want to be possible there. Weathers you leave out can no longer occur in that region. Likelihoods are relative weights, not percentages: `40` and `60` mean 40% and 60%, but `2` and `3` would mean the same thing.

| Field | Type | Notes |
|---|---|---|
| `race` | string | which region to replace, by the race that hosts it |
| `weathers[].weather` | string | `ClearSkies`, `Rain`, `Fog` or `Snow` |
| `weathers[].likelihood` | float | relative weight, zero or more; the list must add up to more than zero |

An entry with an unknown race, an unknown weather or an empty list is skipped with a warning and the region keeps its shipped odds. Weather is rolled per map node from the campaign seed, so a changed table still gives the same weather on every visit to a node.

## Testing your mod

1. Put your mod folder in `Mods/` as described above.
2. Launch the game (or restart it if it was already running).
3. Check the in-game **Mods** menu to confirm it's listed and enabled.
4. Play a battle and confirm the change - the game logs a line for every override file it applies (and warns about anything it couldn't parse) if you need to debug something that isn't working as expected.

If a file has a typo or invalid value, the game skips just that field (or that file, if the whole thing fails to parse) and logs a warning rather than crashing - check the log if something doesn't seem to be applying.
