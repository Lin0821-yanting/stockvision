// 大盤總覽左右滑動的判斷（純函式，方便單元測試）

/** 橫向拖曳超過這個距離才換頁 */
export const SWIPE_THRESHOLD_PX = 60;
/** 移動超過這個距離才判斷是橫向拖曳還是上下捲動 */
export const DRAG_START_PX = 8;

/** 放開時要換到哪個方向：1 下一頁、-1 上一頁、0 不換頁。橫向距離要超過門檻，而且大於垂直距離。 */
export function swipeDirection(dx: number, dy: number, threshold = SWIPE_THRESHOLD_PX): -1 | 0 | 1 {
  if (Math.abs(dx) < threshold || Math.abs(dx) <= Math.abs(dy)) return 0;
  return dx < 0 ? 1 : -1;
}

/** 拖曳中頁面跟著手指移動；第一頁往右拉、最後一頁往左拉時加上阻力，提示已經到底 */
export function dragOffset(dx: number, page: number, pageCount: number): number {
  const pastEdge = (page === 0 && dx > 0) || (page === pageCount - 1 && dx < 0);
  return pastEdge ? dx / 3 : dx;
}

export function clampPage(page: number, pageCount: number): number {
  return Math.min(pageCount - 1, Math.max(0, page));
}
