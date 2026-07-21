# Tabletop Tavern 模组制作指南

Tabletop Tavern 支持通过模组来覆盖单位属性、派系颜色、英雄数据以及英雄/派系的战斗加成——无需编写代码，只需纯文本文件即可。本指南将介绍这些文件的格式。请参阅 [`ExampleMod/`](ExampleMod/) 文件夹，里面有一个完整可用的示例，你可以直接复制并修改。

## 模组的存放位置

模组放在游戏存档目录下的 `Mods` 文件夹中：

- **Windows:** `%USERPROFILE%\AppData\LocalLow\MemoriStudios\TabletopTavern\Mods\`

每个模组都是一个独立的子文件夹：

```
Mods/
    MyModName/
        mod.json              <- required
        unit_overrides.json   <- optional
        race_overrides.json   <- optional
        hero_overrides.json   <- optional
        hero_bonus_rules.json <- optional
```

一个文件夹必须包含 `mod.json` 才会被识别为模组——四个覆盖文件都是可选的，只需包含你需要的文件即可。以下划线 `_` 开头的文件夹名（如 `_Template`）为保留名称，不会被加载为模组。

新模组在游戏首次发现时会自动启用。你可以使用游戏内的 **模组** 菜单（从主菜单进入）来启用/禁用模组并调整其加载顺序——当多个模组修改了相同的内容时，列表中位置更靠下的模组内容会覆盖位置更靠上的模组。 **所有改动不会立即生效，需要在下一次重启游戏时才会应用。**

如果你在 Steam 创意工坊订阅了某个模组，它会在你下次启动游戏时自动同步到本地的 `Mods` 文件夹中——从那一刻起，它的行为就和你手动安装的模组完全一样。

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

`workshopFileId` 留空即可——首次将模组发布到 Steam 创意工坊时，该字段会自动填充，这样后续的发布操作会更新同一个项目，而不会创建重复项。

## `unit_overrides.json` — 单位属性

一个由条目组成的列表，每个条目以 `unitName` 为键。只需包含你想要修改的字段即可；该单位的其他所有属性将保持不变。每个值都以 **字符串** 形式书写，即使是数字和 true/false 也是如此。

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

`unitName` 必须与现有单位的名称完全匹配（区分大小写）——完整列表请参阅下方的 [单位名称参考]。 覆盖一个不存在的 `unitName` 会被静默跳过（并在日志中生成一条警告）——此格式只能修改已有单位，无法添加新单位。

可用字段:

| 字段 | 类型 | 备注 |
|---|---|---|
| `unitType` | enum | 近战`Melee`, 远程`Ranged`, 混合`Hybrid`, 炮兵`Artillery`, 建筑`Structure` |
| `unitSize` | enum | 步兵`Infantry`, 骑兵`Cavalry`, 巨兽`Monstrous`, 单个单位`SingleUnit`, 炮兵`Artillery` |
| `rarityTier` | enum | 普通`Common`, 罕见`Uncommon`, 稀有`Rare`, 传说`Legendary` |
| `meleeAttack`, `meleeDefense`, `weaponStrength`, `armor`, `chargeBonus`, `chargeImpactDamage`, `chargeCount`, `missileStrength`, `ammunition`, `explosionDamage` | int | |
| `hitPointsPerUnit`, `baseUnitCount` | int | 必须为正数——零值或负值会被拒绝，并保留原有数值 |
| `speed`, `leadership`, `baseRange`, `attackAccuracy`, `attackCooldown`, `rateOfFire`, `explosionRange`, `explosionForce` | float | |
| `none`, `standardShields`, `armorPiercing`, `antiInfantry`, `antiLarge`, `terrifying`, `stalwart`, `outrider`, `swampCreature`, `forestDweller`, `chickenFlight`, `ethereal`, `bloodFrenzy`, `rage`, `emblazing`, `unstoppable`, `heavyShields`, `throwingAxes`, `armorSundering`, `monsterSlayer`, `forgefuryTempering`, `flamingAmmo`, `dragonsHoard`, `backStabbers`, `thickScales` | bool | 填写 `"true"` 或 `"false"` |

### 单位名称参考

全部 114 个单位名称，按派系分组，以招募顺序排列（普通单位在前，传奇/怪兽单位在后）。这些名称同样适用于 `hero_overrides.json` 中的 `signatureUnit` 和 `startingArmyUnits`，以及 `hero_bonus_rules.json` 中的 `UnitName` 条件。

**钢铁军团**: `PeasantBowmen`, `LevySwordsmen`, `FieldPikemen`, `LandsknechtGreatswords`, `Arbalesters`, `MilanesePolearms`, `ImperialTemplars`, `DeepwoodRangers`, `BlackEagleHalberdiers`, `BorderlandRiders`, `HearthboundKnights`, `RoyalCavaliers`, `EisenmannRegiment`, `Ashguard`, `KaiserCannon`

**绿潮**: `GoblinRabble`, `GoblinScrapShooters`, `DireWolves`, `OrcRavagers`, `OrcImpalers`, `OrcStalkers`, `BogmawTroll`, `ArmoredDirewolves`, `StonehewerGiant`, `StonegulletEnforcers`, `FleshshredderFanatics`, `Direriders`, `Gobbopult`, `Meatgrinders`, `Siegeclaws`

**渡鸦军团**: `ThrallLevy`, `DriftwoodSkirmishers`, `SeawindSpears`, `Huskarls`, `Shieldmaidens`, `SkogarmadrArchers`, `Berserkers`, `Valkyries`, `VarangianGuard`, `SonsOfFenrir`, `Jomsvikings`, `AngelsOfDeath`, `DraugrBoltThrowers`

**泰伦铎幽林**: `SylvanArchers`, `ForestSpirits`, `AshwoodMilitia`, `AerindelGuard`, `Duskspears`, `MistweaverScouts`, `StarStriders`, `Veilpiercers`, `Treants`, `ElarionSentinels`, `SunspireBladelords`, `VeilkinDrakes`, `LorandelStarhurler`, `EmeraldAncient`

**血色王庭**: `UndeadLevies`, `BoneclatterSpears`, `FeralHounds`, `GravestoneImps`, `DeathhavenFiends`, `Nightriders`, `BoneshardArchers`, `CorpseClaws`, `MistWraiths`, `BlackWardens`, `Bloodsworn`, `BloodswornKnights`, `Shadelords`, `NecroticChimerae`

**樱王朝**: `AshigaruSpearmen`, `RoninWanderers`, `DaikyuCommoners`, `FootSamurai`, `NaginataOnna`, `KunoichiInfiltrators`, `DragonTachi`, `EmperorsArquebusiers`, `Hokoshu`, `KitsuneBlademasters`, `Oni`, `BanryuBombardiers`, `JoseonHwacha`, `GoldenSaru`

**深石堡**: `RiftpickLaborers`, `CrackshotCrossbows`, `Cragflayers`, `HelmwallDefenders`, `DrakefireRiflers`, `GrimfireGuns`, `ThunderhoofChargers`, `GrimazulAncients`, `GlyphstonePhalanx`, `StormForgedBattery`, `TheBulwark`, `AbyssalDelveknights`, `ForgewrathHammers`

**龙蜥部族**: `KoboldBrawlers`, `ScalebowKobolds`, `DireRaptors`, `VenomtailArchers`, `Brutes`, `Redhorns`, `RaptorRiders`, `TriceraPlatform`, `BlackDragon`, `Leviathans`, `StegoplateGuard`, `BloodCarnos`, `Kaiju`, `ObsidianScales`

**特殊** (garrison structures, not recruitable): `ArchersOfApollo`, `Gate`

## `race_overrides.json` — 派系颜色

一个由条目组成的列表，每个条目以 `race`为键。 与单位覆盖不同的是，**三种颜色必须一起指定** — 不能只修改其中一种而保持其他颜色不变，因为在此格式中，颜色没有天然的"未指定"值。

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

`race` 必须是以下之一：`IronLegion`, `Gruntkin`, `RavenHost`, `TaelindorForest`, `SanguineCourt`, `SakuraDynasty`, `DeepstoneHold`, `DrakosaurBrood`。颜色通道取值范围为 0-1 的浮点数，而非 0-255。

通过这种方式只能覆盖颜色——种族的底层模型/预制体以及地图区域无法通过此文件更改。

## `hero_overrides.json` — 英雄阵容数据

一个由条目组成的列表，每个条目以 `heroID` （1-16）为键。与单位覆盖的模式相同，采用稀疏覆盖——只需包含你想要修改的内容即可。

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

| 字段 | 类型 | 备注 |
|---|---|---|
| `heroName`, `heroDescription`, `heroPrefabName` | string | 这些是本地化键值，而非直接的显示文本|
| `heroBonusDescription` | string array | |
| `unlockCondition`, `demoUnlockCondition` | enum | `None`, `NotAvailableInDemo`, `DiscordExclusive`, `NewsletterExclusive`, `HeroCompletion` |
| `startingGold` | int | |
| `signatureUnit` | enum (`UnitName`) | 必须是已存在的单位 |
| `startingArmyUnits` | array of `UnitName` | 任何无法识别的单位名称条目都会被跳过，其余条目仍然生效 |

`heroID` 和英雄的 `race`（派系）无法更改——`heroID` 是查找键，而每个英雄在战役生成时已与其派系永久绑定。

## `hero_bonus_rules.json` — 英雄与派系战斗加成

这是功能最强大也最复杂的一个文件。它用于替换每位英雄在战斗中提供的数值加成（即他们的被动能力），以及已实装的派系全局被动（樱王朝的"全军同种族"加成）。

**重要提示：与其他三个文件不同，规则列表并非逐字段合并。 ** 如果你的文件为某个 `heroID` 写了*任何* `statRules` 条目, 这些条目将**替换该英雄的整套属性规则集**——而不仅仅是在原有基础上添加。 `attributeRules`（针对每位英雄）和 `factionRules`（针对每个派系）也是如此。如果你想调整英雄的某项加成而又不想丢失其他加成，请在你的文件中包含该英雄的所有规则，并在此基础上应用你的修改。

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

### `statRules` 条目字段

| 字段 | 类型 | 备注 |
|---|---|---|
| `heroID` | int | 提供此加成的英雄 |
| `localizationKey` | string | 用于在 UI 中显示加成名称的本地化键值 |
| `condition` | object | 见下方"条件"部分 |
| `stat` | enum (`UnitStat`) | `MeleeAttack`, `MeleeDefense`, `WeaponStrength`, `Accuracy`, `Range`, `MissileStrength`, `Speed`, `Armor`, `ChargeBonus`, `Leadership`, `Ammunition`, `ChargeImpactDamage` |
| `magnitudeKind` | enum | `Flat` (直接加上 `value`) or `PercentOfCurrentValue` (加上 `value` × 该属性的当前值 - 例如 `0.5` 表示 +50%) |
| `value` | float | |

### `attributeRules` 条目字段

与 `statRules` 相同，区别在于没有 `stat`/`magnitudeKind`/`value`字段，取而代之的是一个单独的`grantedAttribute` (enum)——英雄会将此属性赋予符合条件的单位（若该单位尚未拥有此属性）。有效值：`StandardShields`, `ArmorPiercing`, `AntiInfantry`, `AntiLarge`, `Terrifying`, `Stalwart`, `Outrider`, `SwampCreature`, `ForestDweller`, `ChickenFlight`, `Ethereal`, `BloodFrenzy`, `Rage`, `Emblazing`, `Unstoppable`, `HeavyShields`, `ThrowingAxes`, `ArmorSundering`, `MonsterSlayer`, `ForgefuryTempering`, `FlamingAmmo`, `DragonsHoard`, `BackStabbers`, `ThickScales`.

### `factionRules` 条目字段

结构与 `statRules`相同，但以 `race` 而非  `heroID`为键，且没有 `condition` （派系加成在其军队构成要求满足后便会作用于所有单位——目前仅实现了"全军同一种族"这一条件，且只对樱王朝生效）。

### Conditions 条件

每个 `condition` 对象都有一个 `filterKind`字段，根据其取值，还需搭配一到两个额外字段：

| `filterKind` | 额外字段 | 含义 |
|---|---|---|
| `Unconditional` | none | 适用于所有单位 |
| `RarityTier` | `requiredRarityTier`: `Common`/`Uncommon`/`Rare`/`Legendary` | 仅适用于该稀有度的单位 |
| `UnitName` | `unitNames`: array of `UnitName` | 仅适用于列表中列出的单位 |
| `UnitTag` | `tag`: string | 适用于匹配指定标签的单位——目前可用的标签有 `"Goblin"` 和  `"MeleeInfantry"` |
| `UnitType` | `unitTypes`: array of `UnitType` | 适用于所列类型的单位 |
| `UnitSize` | `unitSizes`: array of `UnitSize` | 适用于所列规模的单位 |
| `EnemyRace` | `requiredEnemyRace`: a `Race` | 仅在与该派系作战时生效 |

## 测试你的模组

1. 按照上文所述，将你的模组文件夹放入 `Mods/` 目录中。
2. 启动游戏（如果游戏已在运行，请重启）。
3. 查看游戏内的 **模组** 菜单，确认你的模组已列出并已启用。
4. 进行一场战斗并确认改动是否生效——游戏会为每个已应用的覆盖文件记录一行日志（如果某处无法解析，也会发出警告），方便你在效果不符合预期时进行调试。

如果文件中存在拼写错误或无效值，游戏只会跳过该字段（若整个文件解析失败，则跳过整个文件），并记录一条警告，而不会崩溃——如果发现某些内容似乎没有生效，请检查日志。
