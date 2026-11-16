# Map events (`event_mods.json`)

A mod can add new events to the campaign map. Your events join the game's own in the draw, so a run meets them at
Event nodes like any other event. They use the same panel, dice and rewards. You pick from the game's choice kinds and
reward types below; a mod cannot add new ones.

An event needs two files in your mod folder:

- `event_mods.json` holds the events: when they can appear, their choices and what each result gives.
- `localization_overrides.json` holds their text, the same file you use for any other text.

[`ExampleMod/`](../ExampleMod/) has a complete event, The Lost Caravan, in both files.

## `event_mods.json`

```json
{
    "events": [
        {
            "key": "LostCaravan",
            "minAct": 1,
            "maxAct": 0,
            "races": [],
            "heroes": [],
            "weight": 1,
            "choices": [
                {
                    "kind": "Roll",
                    "rollNeeded": 9,
                    "success":         [ { "type": "Gold", "value": 30 } ],
                    "failure":         [ { "type": "UnitHealth", "value": -0.1 } ],
                    "criticalSuccess": [ { "type": "Gold", "value": 30 }, { "type": "GearDrop" } ],
                    "criticalFailure": [ { "type": "UnitHealth", "value": -0.2 } ]
                },
                {
                    "kind": "Pay",
                    "goldRequired": 15,
                    "success": [ { "type": "NextBattleLeadership", "value": 10 } ]
                },
                {
                    "kind": "WalkAway",
                    "success": [ { "type": "None" } ]
                }
            ]
        }
    ]
}
```

### Event fields

| Field | Type | Notes |
|---|---|---|
| `key` | string | Your name for the event, such as `LostCaravan`. Every text key starts with it (see [Text](#text) below). It may not contain `.` or `/`, end in a digit, or match one of the game's own event keys, and two events in one mod may not share it. (`Ambush1Desc` would be the text of both an event `Ambush1` and choice 1 of an event `Ambush`.) |
| `minAct` | int | The first act the event can appear in, 1 to 3. Leave it out for act 1. |
| `maxAct` | int | The last act it can appear in. Leave it out or write 0 for no limit. |
| `races` | list of strings | Hero factions that can meet it: `IronLegion`, `Gruntkin`, `RavenHost`, `TaelindorForest`, `SanguineCourt`, `SakuraDynasty`, `DeepstoneHold`, `DrakosaurBrood`. Empty means every faction. |
| `heroes` | list of ints | Hero ids (1-16) that can meet it. Empty means every hero. |
| `weight` | number | How likely the event is to be drawn next to the others. The game's own events all have 1, so 2 makes yours twice as likely. Leave it out for 1. |
| `choices` | list | 1 to 10 choices, shown in this order. |

When a run reaches an Event node, the game draws one event from all those the run can meet and has not met yet, the
game's own and every mod's. Once the run has met them all, the list starts over. The March has no Event nodes.

### Choice fields

| Field | Type | Notes |
|---|---|---|
| `kind` | string | `Roll`, `Pay`, `Sacrifice` or `WalkAway` (see below). |
| `rollNeeded` | int | `Roll` only: the number needed on a d20, 1 to 20. |
| `goldRequired` | int | Gold paid when the player picks the choice. A `Pay` choice needs it. A run with less gold sees the choice but cannot pick it. |
| `cost` | list of rewards | What a `Sacrifice` choice takes when the player picks it: a negative `UnitHealth`, `LoseGear`, `LoseSquad` or `LosePrestige`. A run that cannot pay cannot pick it. Gold goes in `goldRequired`, not here. |
| `armySizeRequired` | int | The choice cannot be picked with fewer squads than this. Leave it out for no limit. |
| `requiredRaces` | list of strings | The choice is hidden unless the hero's faction is in this list. |
| `requiredHeroes` | list of ints | Hidden unless the hero's id is in this list. |
| `requiredUnitTypes` | list of strings | Hidden unless the army holds a unit of one of these types: `Melee`, `Ranged`, `Hybrid` or `Artillery`. The type must match exactly, so a `Hybrid` unit does not count as `Ranged`. |
| `requiredGear` | list of strings | Hidden unless the army owns one of these gear items and it is not broken. The names are the `gearID` list in the main guide's `gear_overrides.json` section. |
| `success` | list of rewards | What the player gets on a success. Every kind uses it. |
| `failure`, `criticalSuccess`, `criticalFailure` | list of rewards | `Roll` only: what the other three results give. |

Leave out a requirement list, or leave it empty, to skip it. When you fill in more than one, the run must match each
of them. An empty or missing reward list means "nothing happens", and the panel says so.

**Choice kinds**

- `Roll` throws a d20. A total of `rollNeeded` or more is a success, less is a failure. A total of 20 is a critical
  success and a 1 is a critical failure. As with every event, the player can pay gold to add to the roll, and the
  Renown tree can lower `rollNeeded`.
- `Pay` takes `goldRequired` and gives `success`. No die.
- `Sacrifice` takes its `cost` and gives `success`. No die.
- `WalkAway` costs nothing and gives `success`, which is usually `None`.

**Every event needs one choice that is always open**: no requirement, no `goldRequired`, no `cost` and no
`armySizeRequired`. A `WalkAway` or a plain `Roll` will do. The event panel has no other way out, so without one a
run could be left with nothing to click.

### Reward types

Each reward is `{ "type": "<type>", "value": <number> }`. `NextBattleFixture` also takes a `fixture`.

| `type` | `value` | What it does |
|---|---|---|
| `None` | - | Nothing. The panel says nothing happened. |
| `Gold` | whole number | Gold gained, or lost if negative. |
| `UnitHealth` | -1 to 1 | Every squad gains or loses this share of its max health: `-0.1` is 10% lost, `0.15` heals 15%. |
| `GearDrop` | - | The player can claim one random gear item. |
| `ConsumableDrop` | - | The player can claim one random consumable. |
| `NewUnit` | - | The player can claim one new squad, usually a low rarity one. |
| `PrestigeUnit` | - | A random squad gains a prestige level. |
| `NextBattleLeadership` | whole number | Added to every one of the player's squads' Leadership in the next battle. |
| `NextBattleEnemyLeadership` | whole number | Added to every enemy squad's Leadership in the next battle. Use a positive number to make the next enemy braver. |
| `NextBattleMana` | whole number | Added to the mana for spells in the next battle the player fights. |
| `NextBattleFixture` | - | Puts a building on the next battlefield. `fixture` must be one of `StatueOfBoromid`, `Blacksmith`, `GoblinBarracks`, `GoblinCamp`, `ShrineToTheAllMother` or `Watchtower`. Each one decides for itself which side it helps. |
| `RevealMap` | - | Shows every hidden node ahead. |
| `LoseGear` | - | A random gear item the army owns is lost, with no gold back. |
| `LoseSquad` | - | A random squad leaves the army. The last squad never does. |
| `LosePrestige` | - | A random prestiged squad drops one level. |

`GearDrop`, `ConsumableDrop`, `NewUnit` and `PrestigeUnit` give one each. To give two, list the reward twice. A
`value` on a type that does not use it is ignored.

## Text

Every event needs English (`en`) text for each of its keys in your mod's own `localization_overrides.json`. Other
languages are optional: a language you leave out shows the English. Write the keys with your event's `key` in front,
exactly as below. `<i>` is the choice's place in the list, starting at 0.

| Key | Shown as |
|---|---|
| `<key>Name` | the event's title |
| `<key>Desc` | the event's story text |
| `<key><i>Title` | choice `<i>`'s button |
| `<key><i>Desc` | choice `<i>`'s line under the button |
| `<key><i>SuccessOutcomeDesc` | what happened, after a success (every kind) |
| `<key><i>FailureOutcomeDesc` | after a failure (`Roll` only) |
| `<key><i>CriticalSuccessOutcomeDesc` | after a critical success (`Roll` only) |
| `<key><i>CriticalFailureOutcomeDesc` | after a critical failure (`Roll` only) |

For The Lost Caravan's first choice that is `LostCaravan0Title`, `LostCaravan0Desc`, `LostCaravan0SuccessOutcomeDesc`
and so on:

```json
{
    "overrides": [
        { "locale": "en", "key": "LostCaravanName", "text": "The Lost Caravan" },
        { "locale": "en", "key": "LostCaravan0Title", "text": "Escort Them Out" },
        { "locale": "de", "key": "LostCaravan0Title", "text": "Geleitet sie hinaus" }
    ]
}
```

**Your folder name goes in front of every key.** When the game loads your mod it renames the event to
`<your mod folder>.<key>`, such as `ExampleMod.LostCaravan`, and moves your text with it. You never write the folder
name yourself. This keeps two mods that both have a `LostCaravan` apart, and it still works when players get your mod
from the Steam Workshop, where its folder is named after its Workshop id.

To translate someone else's event, put the full renamed keys in your own `localization_overrides.json`, such as
`ExampleMod.LostCaravanName`, and place your mod below theirs in the Mods menu. The game's log names the folder: look
for the `Events (<folder>)` line.

## What the game checks

Each event is checked when the game starts. An event with a problem is skipped and the log gets one warning that names
the event and the problem. The rest of your mod still loads. The checks:

- `key` is set, has no `.` or `/`, does not end in a digit, is not one of the game's own event keys, and no other
  event in your mod uses it.
- 1 to 10 choices, and at least one is always open (see above).
- `maxAct` is 0 or not below `minAct`, and `weight` is not negative.
- Every `kind`, `type`, faction, unit type, gear and fixture is a name from the lists above, spelled exactly, with
  the same capitals.
- `rollNeeded` is 1 to 20 on a `Roll`. A `Pay` has `goldRequired`, a `Sacrifice` has a `cost`, and a `WalkAway` costs
  nothing.
- `UnitHealth` is between -1 and 1, and `Gold` and the three `NextBattle` numbers are whole numbers.
- Every text key has English text.

When it loads, the log says how many events each mod added: `[ModOverride] Events (MyModName): added 2 event(s).`

## Saves

A run remembers which events it met by name. If a player turns your mod off or removes it, their runs carry on: the
game skips your events from then on. A run that was waiting on a roll in one of your events draws another event at
that node instead.

## Testing

1. Put your event in your mod's `event_mods.json` and its text in `localization_overrides.json`.
2. Restart the game and check the log for the `Events` line and any warnings.
3. Start a run and go to Event nodes. With `weight` set high, such as 50, your event comes up almost every time; set
   it back before you publish.
