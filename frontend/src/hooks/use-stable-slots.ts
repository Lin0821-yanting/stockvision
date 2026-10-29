import { useState } from "react";

function assign(previous: Record<string, number>, items: string[], size: number): Record<string, number> {
  const next: Record<string, number> = {};
  for (const item of items) if (previous[item] !== undefined) next[item] = previous[item];
  const used = new Set(Object.values(next));
  for (const item of items) {
    if (next[item] !== undefined) continue;
    let slot = 0;
    while (used.has(slot) && slot < size - 1) slot += 1;
    next[item] = slot;
    used.add(slot);
  }
  return next;
}

/**
 * 讓顏色跟著股票走：已選的股票保留原本的色槽，新加入的股票用最小的空槽。
 * 移除一檔不會讓其他股票換顏色（dataviz：color follows the entity, never its rank）。
 */
export function useStableSlots(items: string[], size: number): Record<string, number> {
  const key = items.join(",");
  const [state, setState] = useState(() => ({ key, slots: assign({}, items, size) }));
  if (state.key !== key) {
    const slots = assign(state.slots, items, size);
    setState({ key, slots });
    return slots;
  }
  return state.slots;
}
