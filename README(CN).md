# 桌上谈兵模组制作指南

桌上谈兵支持通过模组来覆盖单位属性、派系颜色、英雄数据以及英雄/派系的战斗加成——无需编写代码，只需纯文本文件即可。本指南将介绍这些文件的格式。请参阅 [`ExampleMod/`](ExampleMod/) 文件夹，里面有一个完整可用的示例，你可以直接复制并修改。

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
        gear_overrides.json   <- optional
        army_generation_rules.json <- optional
        economy_overrides.json <- optional
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
| `race` | enum | `IronLegion`, `Gruntkin`, `RavenHost`, `TaelindorForest`, `SanguineCourt`, `SakuraDynasty`, `DeepstoneHold`, `DrakosaurBrood`, `Special` - 将该单位移至该派系的收藏/军表中。不会改变单位的模型、图标或肖像，这些都会保持其原本的样子。 |
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

## `gear_overrides.json` — 装备效果数值

一个由条目组成的列表，每个条目以 `gearID`为键。只有一个字段可以覆盖：`gearModifierValue`，即每件装备效果所基于的数值——武装刀剑的 [近攻]加成、长弓的[射程]加成、普通建造者的金币折扣等等。该数值与装备游戏内提示框中显示的值一致，因此覆盖它会同时更新提示框和实际效果。

```json
{
    "overrides": [
        { "gearID": "ArmingSwords", "gearModifierValue": "10" },
        { "gearID": "Longbows", "gearModifierValue": "35" }
    ]
}
```

如果某件装备的效果是直接解锁某项功能而非数值加成（例如钻锋箭矢赋予 [破甲] 能力、铁库的利息翻倍），则没有有意义的数值可供修改——覆盖这类装备不会产生任何效果，因为没有地方会读取这个值。`gearID` 必须是以下之一：

`ArmingSwords`, `BucklerShields`, `Longbows`, `Glaives`, `ConscriptionOrders`, `TexanBBQ`, `JoustingLances`, `GnomishArmorers`, `DiamondTippedArrows`, `WellHonedAxes`, `RingoftheElvenKing`, `RavensEye`, `BallisticCharts`, `Turkey`, `HeavyWeapons`, `Shungite`, `QuantitativeEasingPolicy`, `TowerShields`, `IronBank`, `OmenofFamine`, `OrnateRing`, `ThePotato`, `Cauldron`, `DwarvenTaxCollectors`, `CommonBuilder`, `UncommonBuilder`, `RareBuilder`, `PrivateeringPapers`, `CookieAndFowlCard`, `BraceletoftheSunGoddess`, `BearSpray`, `LuckyHorseshoe`, `RiverTrout`, `MichaelsSecretStuff`, `Mitre`, `ChugJug`, `PumpkinPie`, `AuraFarming`, `NorthernLooters`, `JailersKey`

通过这种方式只能覆盖数值——装备的名称、稀有度以及是否在商店中禁用无法通过此文件更改。

## `army_generation_rules.json` — 敌方军队与驻军生成

**此文件的工作方式与上述其他文件不同。 ** 单位属性、装备等是你可以逐字段修改的扁平数据。而敌方军队构成是一个分支决策（取决于哪个章节/幕、是否为最终战、你已战斗的次数、难度），因此此文件是一个 **按从上到下顺序匹配的规则列表**——第一个所有条件都匹配的规则胜出。你的规则会在游戏内置规则之前被检查，因此要修改某个特定情况，只需为它编写一条特定规则；你没有覆盖的任何情况都会原封不动地沿用游戏的默认平衡。规则中未填写的字段意味着无论该字段取何值都会匹配。

**请尽可能具体。** 设置的字段越少的规则匹配的情况就越多——例如，一条只设置了 `"board": 1` 的规则 (没有 `finalBattle`，没有战斗次数范围) 将覆盖所有章节一 的情况，包括最终战。下面导出的模板是完全具体的（每个确切情况对应一条规则）——请从中复制你想要更改的行，而不要从头编写规则。

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

这三个数组彼此独立，且均为可选——模组可以只提供其中一个。

### `enemyArmyRules` 条目字段

| 字段 | 类型 | 备注 |
|---|---|---|
| `board` | int | 必填——哪个战役章节/幕 |
| `finalBattle` | bool | 必填 |
| `knightDifficulty` | bool | 可选——省略则匹配任意难度。仅对最终战有意义；原版游戏在普通战斗中忽略此字段 |
| `battlesFoughtMin` | int | 可选——下限（大于等于此值） |
| `battlesFoughtMax` | int | 可选——上限（小于此值）。仅对普通（非最终）战斗有意义；原版游戏在最终战中忽略战斗次数 |
| `tierCounts` | array of `{tier, count}` | 必填——从各单位稀有度等级中抽取多少个编队（1=普通，2=罕见，3=稀有，4=传奇） |

### `townGarrisonRules` 条目字段

| 字段 | 类型 | 备注 |
|---|---|---|
| `townSize` | enum | 必填 —— `Village`（村庄）, `Castle`（城堡）, `City`（城市） |
| `bookNumber` | int | 必填 |
| `difficultyImperator` | bool | 可选——省略则匹配任意难度 |
| `tierCounts` | array of `{tier, count}` | 必填，结构与上文相同 |

### `enemyPrestigeRules` 条目字段

控制生成的敌方编队以已获得威望等级状态出现的概率（公爵难度及以上）。此处没有除幕数和难度以外的条件——所有字段均为必填。

| 字段 | 类型 | 备注 |
|---|---|---|
| `actNumber` | int | 必填 |
| `enhanced` | bool | 必填 - `true` 表示帝王+难度的概率， `false` 表示公爵/男爵难度 |
| `chancePerSquad` | float | 每个编队以晋升状态出现的概率（0-1） |
| `maxPrestigedSquads` | int | 每支军队中晋升编队的数量上限 |
| `prestigeTwoChance` | float | 已升级编队为 2级威望而非 1级的概率（0-1） |

如果没有任何规则（无论是你的还是游戏默认的）匹配到某个棋盘/幕，游戏会自动采用保底方案： `enemyArmyRules`/`townGarrisonRules` 会为该情况生成一支空军队/空驻军（并在日志中记录一条警告——这与未打模组的游戏请求一个不存在的棋盘时的行为一致），而 `enemyPrestigeRules` 会回退到原版游戏 3幕中最接近的那一档，而不是完全禁用晋升机制。这意味着你可以为新添加的章节 4+ 添加规则，而无需同时为其定义晋升规则。

## `economy_overrides.json` — 商店与经济数值

涵盖游戏中的各项金币花费与概率：单位和城镇招募费用、装备和消耗品商店价格、卡包价格、消耗品掉落概率、城镇赏金金币、银行利息，以及战斗/事件的金币奖励。 **以下九个部分彼此独立且均为可选**——模组只需提供自己需要的部分，与 `army_generation_rules.json`一样。

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

### `unitTierCosts` — 按稀有度等级招募单位

| 字段 | 类型 | 备注 |
|---|---|---|
| `tier` | int | 1-4, 1-4，与上文中 `tierCounts` 的等级编号相同（1=普通，2=罕见，3=稀有，4=传奇） |
| `cost` | int | 招募该等级单位所需的金币费用 |

### `townRecruitCosts` — 从城镇招募驻军单位

| 字段 | 类型 | 备注 |
|---|---|---|
| `townSize` | enum | `Village`, `Castle`, `City` ——与上文中 `townGarrisonRules` 的值相同 |
| `cost` | int | |

### `gearRarityCosts` — 在商店购买装备

| 字段 | 类型 | 备注 |
|---|---|---|
| `gearRarity` | enum | 仅限`Common`（普通）, `Uncommon`（罕见）, `Rare`（稀有） ——与消耗品不同，装备没有传奇稀有度 |
| `cost` | int | |

### `consumableRarityCosts` — 在商店购买药水/消耗品

| 字段 | 类型 | 备注 |
|---|---|---|
| `consumableRarity` | enum | `Common`（普通）, `Uncommon`（罕见）, `Rare`（稀有）, `Legendary` （传奇）|
| `cost` | int | |

### `cardPackPrices` — 购买卡包

| 字段 | 类型 | 备注 |
|---|---|---|
| `packID` | int | `0`=Gear Pack, `1`=Card Pack 1, `2`=Card Pack 2, `3`=Card Pack 3, `4`=Card Pack 4 |
| `price` | int | |

### `consumableDropOdds` — 商店/奖励消耗品出现概率

每个条目是一个相对权重（而非百分比），表示该消耗品在当前幕所有可用消耗品中出现的可能性——权重越高越常见。权重只需要彼此相对设置即可，因此你无需为了改变某一项物品的稀有度而重新平衡所有条目。

| 字段 | 类型 | 备注 |
|---|---|---|
| `actNumber` | int | 1-3 |
| `consumable` | enum (`ConsumableEnum`) | `MinorHealth`（小生命）, `MajorHealth`（大生命）, `Prestige`（威望）, `Duplicate`（复制）, `NewUnit`（新单位）, `Alchemist`（炼金）, `Rewind`（回溯）, `TrialofGrasses`（荒草试炼）, `FateshineElixir`（命辉灵药）, `RunewellNectar`（符文井甘露）, `LambSauce`（羊肉酱） |
| `weight` | float | |

### `townBountyRanges` — 城镇掠夺金币

与本文件中其他地方的稀疏字段不同，** `min` 和 `max` 必须一起提供** ——一个范围需要两端都有值才有意义。 `max` 必须大于或等于 `min`，否则该条目会被拒绝（记录为警告）而非应用，因为无效的范围会在下次生成该规模的城镇时导致游戏崩溃。

| 字段 | 类型 | 备注 |
|---|---|---|
| `townSize` | enum | `Village`, `Castle`, `City` |
| `min` | int | 下限（大于等于此值） |
| `max` | int | 上限（小于此值） |

### `bank` — 回合结束利息

单个对象，而非列表。两个字段彼此独立，均为可选。

| 字段 | 类型 | 备注 |
|---|---|---|
| `maxInterest` | int | 每回合通过利息获得的金币上限，不含在此基础上叠加的装备加成（矮人税官、铁库等） |
| `potionRewardsOdds` | int | 战斗后获得额外消耗品的百分比概率（0-100） |

### `battleRewards` — 战后金币

单个对象，而非列表。每个字段彼此独立，均为可选。

| 字段 | 类型 | 备注 |
|---|---|---|
| `ransomCaptivesReward` | int | 每名俘虏的赎金 |
| `skirmishReward` | int | 赢得一场遭遇战的基础金币 |
| `hordeReward` | int | 赢得一场大战的基础金币 |

## 测试你的模组

1. 按照上文所述，将你的模组文件夹放入 `Mods/` 目录中。
2. 启动游戏（如果游戏已在运行，请重启）。
3. 查看游戏内的 **模组** 菜单，确认你的模组已列出并已启用。
4. 进行一场战斗并确认改动是否生效——游戏会为每个已应用的覆盖文件记录一行日志（如果某处无法解析，也会发出警告），方便你在效果不符合预期时进行调试。

如果文件中存在拼写错误或无效值，游戏只会跳过该字段（若整个文件解析失败，则跳过整个文件），并记录一条警告，而不会崩溃——如果发现某些内容似乎没有生效，请检查日志。
