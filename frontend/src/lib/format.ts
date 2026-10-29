import type { Currency, Market } from "@/types/api";

const LOCALE = "zh-TW";
const EMPTY = "—";

export type Tone = "up" | "down" | "flat";

function isNumber(value: number | null | undefined): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

export function formatNumber(value: number | null | undefined, digits = 2): string {
  if (!isNumber(value)) return EMPTY;
  return value.toLocaleString(LOCALE, { minimumFractionDigits: digits, maximumFractionDigits: digits });
}

/** 股價：固定兩位小數，例如 2,415.00 */
export function formatPrice(value: number | null | undefined): string {
  return formatNumber(value, 2);
}

const CURRENCY_PREFIX: Record<Currency, string> = { TWD: "NT$", USD: "US$" };

/** 金額：NT$ 1,000,000（台幣最多兩位小數）、US$ 343.83（美元固定兩位小數） */
export function formatMoney(value: number | null | undefined, currency: Currency = "TWD"): string {
  if (!isNumber(value)) return EMPTY;
  const digits = currency === "USD" ? { minimumFractionDigits: 2, maximumFractionDigits: 2 } : { minimumFractionDigits: 0, maximumFractionDigits: 2 };
  const sign = value < 0 ? "-" : "";
  return `${sign}${CURRENCY_PREFIX[currency]} ${Math.abs(value).toLocaleString(LOCALE, digits)}`;
}

/** 帶正負號的金額：+NT$ 12,000、-NT$ 3,500 */
export function formatSignedMoney(value: number | null | undefined, currency: Currency = "TWD"): string {
  if (!isNumber(value)) return EMPTY;
  return value > 0 ? `+${formatMoney(value, currency)}` : formatMoney(value, currency);
}

export function formatSignedNumber(value: number | null | undefined, digits = 2): string {
  if (!isNumber(value)) return EMPTY;
  const text = formatNumber(Math.abs(value), digits);
  if (value > 0) return `+${text}`;
  if (value < 0) return `-${text}`;
  return text;
}

export function formatPercent(value: number | null | undefined, { signed = true, digits = 2 } = {}): string {
  if (!isNumber(value)) return EMPTY;
  const text = `${formatNumber(Math.abs(value), digits)}%`;
  if (signed && value > 0) return `+${text}`;
  if (value < 0) return `-${text}`;
  return text;
}

/** 大數字縮寫：12,345,678 → 1234.57萬 */
export function formatCompact(value: number | null | undefined): string {
  if (!isNumber(value)) return EMPTY;
  return value.toLocaleString(LOCALE, { notation: "compact", maximumFractionDigits: 2 });
}

/** 成交量：台股以「張」（1 張 = 1,000 股）顯示，美股以「股」顯示 */
export function formatVolume(shares: number | null | undefined, market: Market): string {
  if (!isNumber(shares)) return EMPTY;
  if (market === "TW") return `${Math.round(shares / 1000).toLocaleString(LOCALE)} 張`;
  return `${formatCompact(shares)} 股`;
}

export function formatShares(shares: number | null | undefined): string {
  if (!isNumber(shares)) return EMPTY;
  return `${shares.toLocaleString(LOCALE)} 股`;
}

/** 2026-10-29 → 2026/10/29（只有日期的字串不做時區轉換） */
export function formatDate(value: string | null | undefined): string {
  if (!value) return EMPTY;
  const [year, month, day] = value.slice(0, 10).split("-");
  return year && month && day ? `${year}/${month}/${day}` : EMPTY;
}

/** 2026-10-29 → 10/29 */
export function formatShortDate(value: string): string {
  const [, month, day] = value.slice(0, 10).split("-");
  return `${month}/${day}`;
}

export function formatDateTime(value: string | null | undefined, timeZone = "Asia/Taipei"): string {
  if (!value) return EMPTY;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return EMPTY;
  return date.toLocaleString(LOCALE, {
    timeZone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}

export function formatTime(value: string | null | undefined, timeZone = "Asia/Taipei"): string {
  if (!value) return EMPTY;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return EMPTY;
  return date.toLocaleTimeString(LOCALE, { timeZone, hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false });
}

export function toneOf(value: number | null | undefined): Tone {
  if (!isNumber(value) || value === 0) return "flat";
  return value > 0 ? "up" : "down";
}

/** 台股慣例：上漲紅、下跌綠 */
export const TONE_TEXT_CLASS: Record<Tone, string> = {
  up: "text-up",
  down: "text-down",
  flat: "text-muted-foreground",
};

/** 損益數字的文字顏色：正數紅、負數綠、零維持一般文字色 */
export function signedValueClass(value: number | null | undefined): string {
  const tone = toneOf(value);
  return tone === "flat" ? "" : TONE_TEXT_CLASS[tone];
}

export const TONE_ARROW: Record<Tone, string> = { up: "▲", down: "▼", flat: "－" };
export const TONE_LABEL: Record<Tone, string> = { up: "上漲", down: "下跌", flat: "平盤" };
