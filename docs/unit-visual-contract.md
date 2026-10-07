# Unit visual contract (TJBake phase 1, 2026-10-06)

What a unit's battle visual must provide for the game to drive it, and what the game promises in return. This is
the contract the TJBake baker validates against and the modding guide publishes. The file layout that carries it is
in `unit-json-schema.md`. The plan is the v2 doc linked from `.claude/docs/` index entry for this topic. Every rule
below names the game code that imposes it; verify `file:line` before asserting it.

Status: draft for TJ's review. Decisions it bakes in: 4 bone influences, raw half-float matrices, 1 to 3 variants,
up to 3 LODs, artillery and the Gate excluded, return-to-idle as a slot flag (proposed 2026-10-06, taken here as
accepted until TJ says otherwise).

## 1. What a unit visual is

A unit visual is one **animator root** with these children:

- one or more **body meshes** per LOD level, skinned on the GPU from one shared bone matrix stream;
- zero or more **attachments**: rigid prop meshes that follow a named anchor on the body (helmet, shield, bow);
- for a mounted unit, a **rider**: a second, smaller visual of its own (own meshes, own matrix stream, 3 slots)
  that the game parents to the mount's `saddle` attachment at spawn.

The gameplay entity (health, movement, orders) is not part of the visual. The game instantiates the visual, parents
it under the gameplay root and talks to it through one control component: which slot plays, its speed, and how
fast to blend from the previous slot. Everything else (walking, fighting, dying, outlines, shadows) is the game's
job as long as the visual keeps the shape described here.

## 2. The slot table

Slots are positional. The game reads slot numbers, never clip names. Canonical names are for people and for the
baker's validation messages.

| Slot | Name | Kind | Required for | Who plays it |
| --- | --- | --- | --- | --- |
| 0 | `idle` | loop | all | the return-to-idle target; `WalkRunSystem` when standing |
| 1 | `walk` | loop | all | `WalkRunSystem` under the walk speed threshold |
| 2 | `run` | loop | all | `WalkRunSystem` above the run speed threshold |
| 3 | `meleeStance` | loop | all | `UnitStateMachineSystem` on engage, `BraceStanceSystem`, `RangedMeleeConverterSystem` |
| 4 | `meleeAttack` | one-shot, returns | all | `MeleeUnitAttackSystem`; damage lands on a timer, not on a frame of this clip |
| 5 | `idleVariant1` | one-shot, returns | all | `UnitIdleSystem` at random while idle |
| 6 | `idleVariant2` | one-shot, returns | all | same |
| 7 | `idleVariant3` | one-shot, returns | all | same |
| 8 | `death1` | one-shot, holds | all | `ProcessUnitDeathSystem`, picked at random |
| 9 | `death2` | one-shot, holds | all | same |
| 10 | `death3` | one-shot, holds | all | same |
| 11 | `thrown` | one-shot, returns | all | explosions, spell knockback, melee knockback |
| 12 | `meleeAttackAlt` | one-shot, returns | all | 10% of melee swings |
| 13 | `rangedStance` | loop | `Shoots` or `Casts` | ranged units while aiming |
| 14 | `rangedAttack` | one-shot, returns | `Shoots` or `Casts` | `ShootAnimationEventSystem` on a timer; the mage cast |

"Required for" uses the predicates in `TabletopTavernConstants` (`Shoots`: Ranged, Hybrid, Artillery; `Casts`: Mage).
A melee unit supplies slots 0 to 12. A ranged, hybrid or mage unit supplies 0 to 14. Mages leave 13 as a copy of 3
if they have no aim pose; the game never plays 13 on a mage. A unit may supply the same clip for several slots
(three identical deaths are allowed, three identical idle variants are allowed). `MageCastSystem` checks that the
slot count is above 14 before it plays 14; the slot count is part of the visual.

**Rider slots** (a visual of `kind: "rider"`):

| Slot | Name | Kind |
| --- | --- | --- |
| 0 | `idle` | loop |
| 1 | `attack` | one-shot, returns |
| 2 | `death` | one-shot, holds |

The mount plays its own deaths (8 to 10); the rider plays slot 2 at the same moment and stays attached to the corpse.

## 3. Slot kinds and return-to-idle

Each slot carries two flags in `unit.json`: `loop` and `returnToIdle`. The combinations:

| `loop` | `returnToIdle` | Meaning |
| --- | --- | --- |
| true | false | plays forever (idle, walk, run, stances) |
| false | true | plays once, then the visual returns to the unit's current idle slot |
| false | false | plays once and holds its last frame (deaths) |

A returning slot has `returnAt`, a fraction of the clip (default 0.9). When playback crosses it the runtime raises the
return itself: the unit's visual goes back to the current idle slot, a rider's goes back to its slot 0. **No clip
events exist in this format.** The 2026-10-06 Play check showed the current pipeline's events fire at 0.85 to 1.0;
the hand export of an existing unit copies each event's fraction into `returnAt` so timing is unchanged.

The runtime restarts a one-shot slot whenever a system writes its slot id, even when the id is unchanged. This is
what makes a rider unable to freeze: today's package ignores a write of the same id, so a rider whose return and next
attack land in the same frame holds its last frame (Bug Board, 2026-10-06).

Blending: a slot change blends over `transitionSpeed` seconds, written by the game (0.5 s on spawn, 0 for thrown and
deaths). Looping slots may start at a random phase (`WalkRunSystem` does this so a squad does not march in step).

## 4. Clip rules the baker enforces

- Every required slot is present. A missing slot fails the bake with the slot name.
- Every clip has at least 2 frames and a frame rate of 24, 30 or 60.
- The total frame count across all slots is at most 16384 (one row per frame in the matrix texture).
- The bone count is at most 5461 (3 texels per bone, 16384 texels wide). In practice a Synty rig has 49 to 190.
- A looping clip's last frame should match its first within a tolerance the baker reports as a warning, not an error.
- Deaths end on the ground. The baker cannot check that; the guide says it.
- Clips are sampled on the source `Animator` or `AnimationClip` with root motion off. The visual never moves
  itself; the gameplay entity moves and the visual follows under it.

## 5. Skeleton, mesh and skinning

- One skeleton per unit. All variants and all LODs share it and share one matrix stream (`anim.bin`).
- A body mesh carries 4 bone influences per vertex (indices and normalized weights). The baker renormalizes rigs
  authored with more and drops the smallest weights.
- Mesh space is the unit's model space: Y up, forward +Z, feet at Y 0, metres. Every unit spawns from
  `Base Unit.prefab` with collision radius 0.75; a visual wider than about 1.5 m at the feet overlaps its neighbours.
  Size tables for cavalry, monstrous and artillery live in `TabletopTavernConstants` (`UnitSize`), not in the visual.
- Each body mesh carries an **animation-inclusive bounds box**: the union of its vertex positions over every frame of
  every slot, padded by 5%. Entities Graphics culls by this box and `AddComponents` resets it to the bind-pose box,
  so the builder writes it afterwards. A box that is too small makes a dying or thrown unit vanish at the screen edge
  and lose its shadow.
- Normals and tangents are skinned with the position. Vertex colour is not used.

## 6. Anchors and attachments

An anchor is a named bone-space point whose model-space matrix is written per frame (`anchors.bin`). Attachments
are rigid meshes that follow one anchor. The game cares only about **roles**:

| Role | What the game does with it | Hierarchy the builder makes | Marker component |
| --- | --- | --- | --- |
| `bow` | hidden by `Scale` 0 while the unit fights in melee, shown again at range (`RangedMeleeConverterSystem`); `BowSetUpSystem` finds it three hops up | anchor follower entity, then the mesh entity under it | `BowSetUpEntity` on the mesh entity |
| `sword` | shown only in melee; `SwordSetUpSystem` hides it at spawn; three hops | anchor follower, then mesh | `SwordSetUpEntity` on the mesh entity |
| `shield` | arrow impacts parent to it (`BlockArrowSystem`); `ShieldSetUpSystem` finds it two hops up; `ShieldRandomizerSystem` may swap its mesh | anchor follower that carries the mesh itself | `ShieldSetUpEntity` on the follower |
| `saddle` | the rider is parented here at spawn (`SaddleSetUpSystem`); two hops | anchor follower that carries the (usually invisible) seat mesh | `SaddleSetUpEntity` on the follower |
| `prop` | nothing; purely visual (helmet, beard, shoulders, cape, staff, book) | anchor follower that carries the mesh | none |

Rules:

- Anchor names are free text; roles are the fixed set above, at most one of each per variant except `prop`.
- **Bow and sword match the built-in unit.** The swap is gameplay: it is what stops a ranged unit shooting in melee,
  and it only runs when both props exist. So a variant has one `bow` and one `sword` exactly when the built-in unit
  swaps (15 of the 23 ranged and hybrid units, checked 2026-10-06), and never both otherwise. The game checks this
  at battle load against the built-in variant 0, because the built-in props are not known before then.
- A mounted unit needs one `saddle`, whether it ships its own rider or keeps the built-in one.
- An attachment can be per variant (Helmwall's three variants differ only by prop meshes) and can list which LODs
  show it. Default: shown at LOD0 and LOD1, hidden at LOD2.
- Attachments do not cast shadows separately from the body in today's pipeline either; they inherit the body's
  shadow setting.
- The rider's own attachments (lance, helmet) are attachments of the rider visual, not of the mount.

## 7. Hierarchy the game assumes

The runtime builder constructs exactly this and nothing else may rely on more:

```text
gameplay root (baked, unchanged)
  animator root            <- AnimationDataHolder.gpuEcsAnimatorEntity; free LocalTransform
    LOD group entity       <- MeshLODGroupComponent
    body mesh entity(s)    <- one per mesh per LOD, MeshLODComponent, RenderBounds
    attachment follower(s) <- one per attachment, follows its anchor matrix
      prop mesh entity     <- only for roles bow and sword
```

What the game writes or reads on this tree:

- `ReturnToIdleEventHandlerSystem` walks one `Parent` from the animator root to the gameplay root. The new runtime
  replaces it with the slot flag, but the adapter keeps the old path for the old package until phase 7.
- `UnitRecoilSystem` moves the animator root's `LocalTransform` for hit feedback. `ProcessUnitDeathSystem` composes the
  corpse pose into it and unparents the corpse. Nothing else may write it.
- `UnitOutlineSystem` walks `Child` from the animator root and sets rendering layer bits on every renderer below it.
- Set-up systems walk fixed hop counts (section 6). Extra levels break them.
- `ArtilleryCrewPrefabGO` polls the current slot id of the artillery dummy. Artillery is out of scope for reskins,
  but the adapter keeps a readable current slot id on every visual.

## 8. Variants, LODs, rider

- **Variants:** 1 to 3. The spawn code picks one by `index % count`. All variants share skeleton, slots and matrix
  stream; they differ in body meshes, materials and attachments.
- **LODs:** up to 3 levels per variant, LOD0 required. Each level lists its body meshes. Switch heights are
  screen-height fractions authored for lodBias 1; the project runs lodBias 2, which doubles the distances. Defaults:
  LOD1 at 0.10, LOD2 at 0.04, no cull level. Entities Graphics has no LOD crossfade; the switch is a hard cut.
- **Rider:** optional, only for a `UnitSize.Cavalry` unit that has a rider today (12 units, hardcoded in
  `UnitSetUpSystem`). A reskin may ship its own rider or keep the built-in one by leaving `rider` out. A unit with no
  built-in rider may not ship one. A rider visual
  has the 3-slot table, its own anchors and attachments, and no LODs (riders are small).

## 9. Materials and shader

- A body material is: base colour texture (PNG), optional normal map, optional emission texture, a colour tint, a
  smoothness value, and a `transparent` flag. The game's unit shader is URP Lit based, opaque, Forward+, casts
  shadows, and has a DepthOnly pass because `UnitOutlineFeature` renders depth-only lists for the hover and selection
  outline. The transparent variant exists for the Mist Wraith style units; use it only when needed, it sorts.
- Per-instance data the game writes: the animation state (which frame pair and blend) and an enable flag. The visual
  never sets a material property itself.
- Team colour is not in the material. Markers and flags carry it. Hit flash, dissolve and tint do not exist.
- The Collection's undiscovered state swaps every renderer's material for one grey material. The preview player
  must allow that swap and keep animating.

## 10. Out of scope, by decision

- Artillery and the Gate: one invisible dummy animator drives Mecanim crew GameObjects. Not GPU-skinned.
- The Death Angels' nested Horse Wings animator. A reskin replaces the whole visual, built-in wings included, so a
  winged reskin puts the wing bones in its own skeleton and animates them in the same clips. TJBake bakes one Animator.
- New roster entries, runtime glTF import, spell and projectile visuals.
- Changing a unit's size class, collision radius or stats through the visual.

## 11. What the game promises a conforming visual

- It is loaded per battle for every `UnitName` the mod overrides, through `UnitGPUAnimLoader`, and every spawn path
  (`SpawnManager`, `ArmySpawnManager`, `SaddleSetUpSystem`) picks it over the built-in one with no further hook.
- It is destroyed at battle cleanup. Nothing of it survives a state change.
- A file that fails validation logs one error naming the file and the rule, and the built-in visual loads instead.
  The manifest and the rules that need the unit's stats are checked at boot; the meshes, the rider rule and the bow
  and sword rule at battle load. A bad file never throws inside the battle load chain.
- Built-in variant 0 (and the built-in rider) still load for a modded unit: they decide the bow and sword rule and
  are the fallback. On a refusal all three variant slots use built-in variant 0.
- The recruit screen, the Prestige picker and the Collection codex show the same files through the TJBake preview
  player, placed with the built-in recruit prefab's root position, turn and scale. `icon.png` (256x256) replaces the
  unit's card icon everywhere it is drawn.

## 12. Source files behind each rule

| Rule | File |
| --- | --- |
| Slot ids 0 to 12 | `ECS/Authoring/AnimationDataHolderAuthoring.cs:23-41` |
| Slots 13, 14, cavalry death 2, mage cast 14 | `ECS/Components/TabletopTavernConstants.cs:24-30`, `RangedMeleeConverterSystem.cs:70-71` |
| Who plays which slot | `WalkRunSystem.cs:41-62`, `UnitStateMachineSystem.cs:112-126, 200-203`, `IdleAnimationsSystem.cs:46-56`, `MeleeUnitAttackSystem.cs:117-130, 220-228`, `ShootAnimationEventSystem.cs:20-24`, `ProcessUnitDeathSystem.cs:93-124`, `ExplosionSystem.cs:143-152`, `SpellSystem.cs:183-186`, `BraceStanceSystem.cs:61-71`, `MageCastSystem.cs:205-220` |
| Return-to-idle today | `IdleAnimationsSystem.cs:67-107` |
| Hop counts and markers | `BowSetUpSystem.cs:14-40`, `SwordSetUpSystem.cs:20-45`, `ShieldSetUpSystem.cs:25-41`, `SaddleSetUpSystem.cs:22-60`, `BlockArrowSystem.cs:30-32` |
| Prop hide by scale | `RangedMeleeConverterSystem.cs:43-49, 78-84`, `SwordSetUpSystem.cs:41-43` |
| Visual root transform writers | `UnitRecoilSystem.cs:54-82`, `ProcessUnitDeathSystem.cs:106-111` |
| Outline | `ECS/Systems/UnitOutlineSystem.cs:80-113`, `Battle/Visuals/UnitOutlineFeature.cs` |
| Variants and the loader seam | `ECS/Authoring/UnitGPUAnimAuthoring.cs:76-90`, `Battle/Units/UnitGPUAnimLoader.cs` |
| Cavalry list | `UnitSetUpSystem.cs:331-349` |
| Previews | `RecruitmentScene.cs:46-49`, `RecruitCard.cs:79-82`, `PrestigeTraitPanel.cs:196-224`, `CollectionPreviewRig.cs:79-114` |
| Bounds and LOD facts | Entities Graphics 1.4.21 `RenderMeshUtility.cs:274, 321`, `LODRequirementsUpdateSystem.cs:323` |
