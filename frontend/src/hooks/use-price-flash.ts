import { useState } from "react";

export type FlashDirection = "up" | "down" | null;

/**
 * 價格變動時回傳新的 key 與方向；元件用 key 重新掛載閃爍動畫。
 * 以「渲染時比較上一次的值」更新狀態（React 文件建議的 derived state 寫法），不需要 effect。
 */
export function usePriceFlash(price: number | null | undefined): { key: number; direction: FlashDirection } {
  const [state, setState] = useState<{ price: number | null | undefined; key: number; direction: FlashDirection }>({
    price,
    key: 0,
    direction: null,
  });

  if (price !== state.price) {
    const direction = price != null && state.price != null ? (price > state.price ? "up" : "down") : null;
    setState({ price, key: state.key + 1, direction });
  }

  return { key: state.key, direction: state.direction };
}
