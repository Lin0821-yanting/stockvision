// 與後端 Pydantic 規則一致的前端表單檢查（後端仍會再驗證一次）

export const USERNAME_RULE = /^[A-Za-z0-9_]{3,30}$/;
export const MIN_PASSWORD = 8;
export const MAX_PASSWORD = 128;

export function validateUsername(value: string): string | null {
  return USERNAME_RULE.test(value.trim()) ? null : "帳號需為 3–30 個英文字母、數字或底線";
}

export function validatePassword(value: string): string | null {
  if (value.length < MIN_PASSWORD) return `密碼至少需要 ${MIN_PASSWORD} 個字元`;
  if (value.length > MAX_PASSWORD) return `密碼最多 ${MAX_PASSWORD} 個字元`;
  return null;
}

export type RegistrationErrors = Partial<Record<"username" | "password" | "confirm", string>>;

export function validateRegistration(input: { username: string; password: string; confirm: string }): RegistrationErrors {
  const errors: RegistrationErrors = {};
  const username = validateUsername(input.username);
  const password = validatePassword(input.password);
  if (username) errors.username = username;
  if (password) errors.password = password;
  if (input.password !== input.confirm) errors.confirm = "兩次輸入的密碼不一致";
  return errors;
}

/** 登入後要導回的頁面：只接受站內路徑，避免被拿來導向外部網站 */
export function safeNextPath(next: string | null | undefined): string {
  if (!next || !next.startsWith("/") || next.startsWith("//") || next.includes("\\") || next.includes("://")) return "/";
  if (next === "/login" || next.startsWith("/login?")) return "/";
  return next;
}
