// HIGHFLY WORLD7 / P70-B — identity for OFFLINE session compatibility.
// This layer intentionally does NOT mutate the game's legacy class, stats,
// equipped skills, resources, attack authority, saves or network protocol.
// The only source of truth for RPG gameplay remains the existing Sim.
export interface HighflyUniversalHunterIdentity {
  readonly kind: 'universal-hunter';
  readonly displayName: string;
  readonly visualSkinIndex: number;
  readonly allowedStats: readonly ['STR', 'AGI', 'VIT', 'PER', 'INT'];
  readonly allowedResources: readonly ['HP', 'MP', 'ENERGIA'];
  readonly activeSlots: 4;
  readonly passiveSlots: 1;
}

const sessions = new WeakMap<object, HighflyUniversalHunterIdentity>();

export function defineHighflyHunterIdentity(
  displayName: string, visualSkinIndex: number
): HighflyUniversalHunterIdentity {
  const name = displayName.trim();
  if (!name || name.length > 48) throw new Error('HIGHFLY_BAD_HUNTER_NAME');
  if (!Number.isSafeInteger(visualSkinIndex) || visualSkinIndex < 0 || visualSkinIndex > 4096)
    throw new Error('HIGHFLY_BAD_HUNTER_SKIN');
  const allowedStats = Object.freeze(['STR','AGI','VIT','PER','INT'] as const);
  const allowedResources = Object.freeze(['HP','MP','ENERGIA'] as const);
  return Object.freeze({
    kind: 'universal-hunter' as const,
    displayName: name,
    visualSkinIndex,
    allowedStats, allowedResources,
    activeSlots: 4 as const,
    passiveSlots: 1 as const,
  });
}

export function registerHighflyHunterSession(
  sim: object, identity: HighflyUniversalHunterIdentity
): void {
  if (!sim || typeof sim !== 'object') throw new Error('HIGHFLY_MISSING_SIM');
  if (sessions.has(sim)) throw new Error('HIGHFLY_SESSION_ALREADY_TRACKED');
  sessions.set(sim, identity);
}

export function getHighflyHunterSession(
  sim: object
): HighflyUniversalHunterIdentity | null {
  return sessions.get(sim) ?? null;
}

// Future migration adapters must consult the real simulation for level/stats.
// In particular, this module MUST NOT introduce a parallel progression save.
