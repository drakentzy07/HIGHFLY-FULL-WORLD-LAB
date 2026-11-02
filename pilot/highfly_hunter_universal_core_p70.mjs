// HIGHFLY WORLD 7 / P70: classless hunter domain core.
// Standalone, dependency-free ESM. NOT wired into the private stage or Sim yet.
// No ClaudeCraft class is inferred from the selected KayKit skin.
export const STATS = Object.freeze(['STR', 'AGI', 'VIT', 'PER', 'INT']);
export const RESOURCES = Object.freeze(['hp', 'mp', 'energy']);
export const ACTIVE_SLOTS = Object.freeze(['S1', 'S2', 'S3', 'S4']);
export const AIM_SHAPES = Object.freeze(['line', 'cone', 'circle', 'target', 'self']);

function assertId(value, field) {
  if (typeof value !== 'string' || !value.trim()) {
    throw new Error('HIGHFLY_INVALID_' + field);
  }
  return value.trim();
}
function statBlock(values, keys, label) {
  if (!values || typeof values !== 'object') throw new Error('HIGHFLY_MISSING_' + label);
  const result = {};
  for (const k of keys) {
    if (!Number.isFinite(values[k]) || values[k] < 0) {
      throw new Error('HIGHFLY_INVALID_' + label + '_' + k);
    }
    result[k] = values[k];
  }
  return Object.freeze(result);
}
function frozenHunter(hunter) {
  return Object.freeze(hunter);
}

// Starting stats/resources must come from one game-wide balance configuration;
// never from a skin's name, rig, weapon, or legacy class.
export function createHunter({ id, name, skinId, startingStats, startingResources }) {
  return frozenHunter({
    id: assertId(id, 'ID'),
    name: assertId(name, 'NAME'),
    skinId: assertId(skinId, 'SKIN'),
    level: 1,
    xp: 0,
    baseStats: statBlock(startingStats, STATS, 'STATS'),
    resources: statBlock(startingResources, RESOURCES, 'RESOURCES'),
    learnedSkills: Object.freeze([]),
    activeSkills: Object.freeze({ S1: null, S2: null, S3: null, S4: null }),
    passiveSkill: null,
  });
}

export function selectSkin(hunter, skinId) {
  return frozenHunter({ ...hunter, skinId: assertId(skinId, 'SKIN') });
}

// Only an explicit acquisition event may teach a skill. A visual skin does not.
export function learnSkill(hunter, skillId, catalog) {
  const id = assertId(skillId, 'SKILL');
  if (!catalog || !Object.hasOwn(catalog, id)) throw new Error('HIGHFLY_UNKNOWN_SKILL');
  if (hunter.learnedSkills.includes(id)) return hunter;
  return frozenHunter({
    ...hunter,
    learnedSkills: Object.freeze([...hunter.learnedSkills, id]),
  });
}

export function equipSkill(hunter, skillId, slot, catalog) {
  const id = assertId(skillId, 'SKILL');
  const def = catalog?.[id];
  if (!def || !hunter.learnedSkills.includes(id)) {
    throw new Error('HIGHFLY_SKILL_NOT_LEARNED');
  }
  if (slot === 'PASSIVE') {
    if (def.kind !== 'passive') throw new Error('HIGHFLY_SLOT_KIND_MISMATCH');
    return frozenHunter({ ...hunter, passiveSkill: id });
  }
  if (!ACTIVE_SLOTS.includes(slot) || def.kind !== 'active') {
    throw new Error('HIGHFLY_SLOT_KIND_MISMATCH');
  }
  return frozenHunter({
    ...hunter,
    activeSkills: Object.freeze({ ...hunter.activeSkills, [slot]: id }),
  });
}

export function unequipSkill(hunter, slot) {
  if (slot === 'PASSIVE') return frozenHunter({ ...hunter, passiveSkill: null });
  if (!ACTIVE_SLOTS.includes(slot)) throw new Error('HIGHFLY_INVALID_SLOT');
  return frozenHunter({
    ...hunter,
    activeSkills: Object.freeze({ ...hunter.activeSkills, [slot]: null }),
  });
}

// Skill eligibility is derived from learned knowledge + level, weapon and resources.
// No 'warrior', 'mage', or other class gate is consulted.
export function canUseSkill(hunter, skillId, catalog, equippedWeaponType) {
  const def = catalog?.[skillId];
  if (!def || !hunter.learnedSkills.includes(skillId)) return false;
  if (def.kind !== 'active') return false;
  if (hunter.level < (def.minLevel ?? 1)) return false;
  if (Array.isArray(def.weaponTypes) && !def.weaponTypes.includes(equippedWeaponType)) {
    return false;
  }
  const cost = def.cost ?? {};
  return RESOURCES.every(k => (cost[k] ?? 0) <= hunter.resources[k]);
}

export function skillAimShape(skillId, catalog) {
  const def = catalog?.[skillId];
  if (!def || def.kind !== 'active') return null;
  return AIM_SHAPES.includes(def.aimShape) ? def.aimShape : null;
}

// Additive gear is derived at read-time; neither items nor skins mutate baseStats.
export function effectiveStats(hunter, equipmentBonus = {}) {
  const bonus = statBlock(
    Object.fromEntries(STATS.map(k => [k, equipmentBonus[k] ?? 0])),
    STATS, 'EQUIPMENT',
  );
  return Object.freeze(
    Object.fromEntries(STATS.map(k => [k, hunter.baseStats[k] + bonus[k]])),
  );
}

// The rig must actually contain the chosen clip. Never invent an animation.
// Mapping format: { sword: { atk1:['Sword_Slash_A'], run:['Running_A'] },
//                   default: { idle:['Idle_A'] } }.
export function resolveAnimation(action, weaponType, availableClips, mapping) {
  const wanted = assertId(action, 'ACTION');
  const clips = availableClips instanceof Set ? availableClips : new Set(availableClips ?? []);
  const variants = [
    ...(mapping?.[weaponType]?.[wanted] ?? []),
    ...(mapping?.default?.[wanted] ?? []),
  ];
  for (const clip of variants) {
    if (typeof clip === 'string' && clips.has(clip)) {
      return Object.freeze({ ok: true, clip, action: wanted, weaponType });
    }
  }
  return Object.freeze({ ok: false, clip: null, action: wanted, weaponType,
    reason: 'MISSING_COMPATIBLE_ANIMATION' });
}

// The core deliberately does NOT apply damage, physics, cooldowns or save migration.
// Those must remain authoritative in the real Sim and be wired via tested adapters.
