# Tabletop Tavern Modding Guide

Tabletop Tavern supports mods that override unit stats, faction colors, hero data, hero/faction battle bonuses, gear effect magnitudes, shop/economy pricing, and enemy army/garrison generation — no code required, just plain text files. This guide covers the file formats. See the [`ExampleMod/`](ExampleMod/) folder for a complete, working example you can copy and edit.

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
```

A folder needs `mod.json` to be recognized as a mod at all — the seven override files are each optional, include only the ones you need. Folder names starting with `_` (like `_Template`) are reserved and never loaded as mods.

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
| `race` | enum | `IronLegion`, `Gruntkin`, `RavenHost`, `TaelindorForest`, `SanguineCourt`, `SakuraDynasty`, `DeepstoneHold`, `DrakosaurBrood`, `Special` - moves the unit to that faction's collection/army-builder roster. Doesn't change the unit's model, icon, or portrait, which stay whatever they were originally. |
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

Note: only `magnitudeKind: "Flat"` is meaningful here. Unlike hero stat rules, the faction path has no current-stat value to scale against, so `PercentOfCurrentValue` is ignored - the raw `value` is added as a flat amount instead (logged as a warning). Author faction bonuses as flat values.

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
| `consumable` | enum (`ConsumableEnum`) | `MinorHealth`, `MajorHealth`, `Prestige`, `Duplicate`, `NewUnit`, `Alchemist`, `Rewind`, `TrialofGrasses`, `FateshineElixir`, `RunewellNectar`, `LambSauce` |
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

## Testing your mod

1. Put your mod folder in `Mods/` as described above.
2. Launch the game (or restart it if it was already running).
3. Check the in-game **Mods** menu to confirm it's listed and enabled.
4. Play a battle and confirm the change - the game logs a line for every override file it applies (and warns about anything it couldn't parse) if you need to debug something that isn't working as expected.

If a file has a typo or invalid value, the game skips just that field (or that file, if the whole thing fails to parse) and logs a warning rather than crashing - check the log if something doesn't seem to be applying.
