import test from 'node:test';
import assert from 'node:assert/strict';
import {
  createHunter, selectSkin, learnSkill, equipSkill, unequipSkill,
  canUseSkill, skillAimShape, effectiveStats, resolveAnimation,
} from '../pilot/highfly_hunter_universal_core_p70.mjs';

const start = Object.freeze({ STR: 10, AGI: 10, VIT: 10, PER: 10, INT: 10 });
const pools = Object.freeze({ hp: 100, mp: 60, energy: 80 });
const catalog = Object.freeze({
  fireball: { kind: 'active', minLevel: 1, aimShape: 'line', cost: { mp: 12 } },
  rush: { kind: 'active', minLevel: 3, aimShape: 'target',
    weaponTypes: ['sword'], cost: { energy: 10 } },
  aura: { kind: 'passive', minLevel: 1 },
});
const make = skinId => createHunter({
  id: 'hunter-1', name: 'Draken', skinId, startingStats: start, startingResources: pools,
});

test('different KayKit skins share an identical level-one start', () => {
  const knight = make('kaykit-knight');
  const rogue = make('kaykit-rogue');
  assert.deepEqual(knight.baseStats, rogue.baseStats);
  assert.deepEqual(knight.resources, rogue.resources);
  assert.equal(knight.level, rogue.level);
  assert.equal(knight.xp, rogue.xp);
  assert.equal(knight.learnedSkills.length, 0);
  assert.equal(knight.activeSkills.S1, null);
  assert.equal(Object.hasOwn(knight, 'class'), false);
});

test('changing skin does not alter attributes, knowledge or loadout', () => {
  const learned = learnSkill(make('kaykit-knight'), 'fireball', catalog);
  const equipped = equipSkill(learned, 'fireball', 'S1', catalog);
  const swapped = selectSkin(equipped, 'kaykit-mage');
  assert.equal(swapped.skinId, 'kaykit-mage');
  assert.deepEqual(swapped.baseStats, equipped.baseStats);
  assert.deepEqual(swapped.resources, equipped.resources);
  assert.deepEqual(swapped.learnedSkills, equipped.learnedSkills);
  assert.deepEqual(swapped.activeSkills, equipped.activeSkills);
  assert.equal(equipped.skinId, 'kaykit-knight');
});

test('skills are learned explicitly and do not come from the skin', () => {
  const hunter = make('kaykit-mage');
  assert.equal(canUseSkill(hunter, 'fireball', catalog, 'staff'), false);
  const learned = learnSkill(hunter, 'fireball', catalog);
  assert.equal(canUseSkill(learned, 'fireball', catalog, 'staff'), true);
  assert.deepEqual(learned.learnedSkills, ['fireball']);
  assert.deepEqual(hunter.learnedSkills, []);
});

test('four active slots and one passive slot reject wrong types', () => {
  let h = learnSkill(make('kaykit-knight'), 'fireball', catalog);
  h = learnSkill(h, 'aura', catalog);
  h = equipSkill(h, 'fireball', 'S4', catalog);
  h = equipSkill(h, 'aura', 'PASSIVE', catalog);
  assert.equal(h.activeSkills.S4, 'fireball');
  assert.equal(h.passiveSkill, 'aura');
  assert.throws(() => equipSkill(h, 'aura', 'S1', catalog), /SLOT_KIND/);
  assert.throws(() => equipSkill(h, 'fireball', 'PASSIVE', catalog), /SLOT_KIND/);
  assert.equal(unequipSkill(h, 'S4').activeSkills.S4, null);
});

test('weapon and level gating is independent of skin', () => {
  const hunter = learnSkill(make('kaykit-rogue'), 'rush', catalog);
  assert.equal(canUseSkill(hunter, 'rush', catalog, 'sword'), false);
  const advanced = Object.freeze({ ...hunter, level: 3 });
  assert.equal(canUseSkill(advanced, 'rush', catalog, 'staff'), false);
  assert.equal(canUseSkill(advanced, 'rush', catalog, 'sword'), true);
});

test('all five aim shapes can be declared without a legacy class', () => {
  for (const shape of ['line', 'cone', 'circle', 'target', 'self']) {
    assert.equal(skillAimShape('skill', { skill: {kind:'active', aimShape:shape} }), shape);
  }
  assert.equal(skillAimShape('skill', { skill: {kind:'active', aimShape:'unknown'} }), null);
});

test('equipment bonuses never mutate the base progression', () => {
  const hunter = make('kaykit-knight');
  const eff = effectiveStats(hunter, { STR: 5, PER: 2 });
  assert.equal(eff.STR, 15);
  assert.equal(eff.PER, 12);
  assert.equal(hunter.baseStats.STR, 10);
  assert.equal(hunter.baseStats.PER, 10);
  assert.equal(Object.isFrozen(hunter.baseStats), true);
});

test('animation resolver uses only loaded clips and tolerates absent variants', () => {
  const mapping = { sword: { atk1: ['Sword_Attack_1'] },
    default: { idle: ['Idle'], atk1: ['AttackFallback'] } };
  const hit = resolveAnimation('atk1', 'sword', ['Sword_Attack_1'], mapping);
  assert.equal(hit.ok, true);
  assert.equal(hit.clip, 'Sword_Attack_1');
  const missing = resolveAnimation('atk1', 'bow', ['Idle'], mapping);
  assert.equal(missing.ok, false);
  assert.equal(missing.clip, null);
  assert.equal(missing.reason, 'MISSING_COMPATIBLE_ANIMATION');
});

test('invalid starter blocks fail closed rather than using warrior defaults', () => {
  assert.throws(() => createHunter({ id:'h', name:'H', skinId:'s',
    startingStats:{ STR:2 }, startingResources:pools }), /INVALID_STATS/);
  assert.throws(() => createHunter({ id:'h', name:'H', skinId:'s',
    startingStats:start, startingResources:{hp:100} }), /INVALID_RESOURCES/);
});
