"use client";

import { useEffect, useId, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { LoaderCircle, LogIn, ShieldCheck, UserPlus } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useAuth } from "@/hooks/use-auth";
import type { AuthMode } from "@/hooks/use-login-href";
import { safeNextPath, validateRegistration, validateUsername, type RegistrationErrors } from "@/lib/validation";
import { ApiError, errorMessage } from "@/services/api-client";

function Field({
  id,
  label,
  error,
  hint,
  ...props
}: React.ComponentProps<typeof Input> & { id: string; label: string; error?: string; hint?: string }) {
  const describedBy = error ? `${id}-error` : hint ? `${id}-hint` : undefined;
  return (
    <div className="space-y-1.5">
      <Label htmlFor={id}>{label}</Label>
      <Input id={id} aria-invalid={error ? true : undefined} aria-describedby={describedBy} {...props} />
      {error ? (
        <p id={`${id}-error`} className="text-xs text-destructive">
          {error}
        </p>
      ) : hint ? (
        <p id={`${id}-hint`} className="text-xs text-muted-foreground">
          {hint}
        </p>
      ) : null}
    </div>
  );
}

function FormError({ message }: { message: string | null }) {
  if (!message) return null;
  return (
    <p role="alert" className="rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive">
      {message}
    </p>
  );
}

function LoginForm() {
  const id = useId();
  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!username.trim() || !password) {
      setError("請輸入帳號與密碼");
      return;
    }
    setPending(true);
    setError(null);
    try {
      const result = await login(username.trim(), password);
      toast.success(result.message);
    } catch (caught) {
      setError(errorMessage(caught));
      setPending(false);
    }
  }

  return (
    <form onSubmit={submit} className="space-y-4" noValidate data-testid="login-form">
      <Field
        id={`${id}-username`}
        label="帳號"
        autoComplete="username"
        autoCapitalize="none"
        spellCheck={false}
        value={username}
        onChange={(event) => setUsername(event.target.value)}
        autoFocus
      />
      <Field
        id={`${id}-password`}
        label="密碼"
        type="password"
        autoComplete="current-password"
        value={password}
        onChange={(event) => setPassword(event.target.value)}
      />
      <FormError message={error} />
      <Button type="submit" className="w-full" disabled={pending}>
        {pending ? <LoaderCircle className="animate-spin" /> : <LogIn />}
        登入
      </Button>
    </form>
  );
}

function RegisterForm() {
  const id = useId();
  const { register } = useAuth();
  const [values, setValues] = useState({ username: "", displayName: "", password: "", confirm: "" });
  const [fieldErrors, setFieldErrors] = useState<RegistrationErrors>({});
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  function update(field: keyof typeof values, value: string) {
    setValues((current) => ({ ...current, [field]: value }));
    if (field in fieldErrors) setFieldErrors((current) => ({ ...current, [field]: undefined }));
  }

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const errors = validateRegistration(values);
    setFieldErrors(errors);
    setError(null);
    if (Object.keys(errors).length) return;
    setPending(true);
    try {
      const result = await register(values.username.trim(), values.password, values.displayName);
      toast.success(result.message, { description: "已自動登入，並建立 NT$1,000,000 的模擬帳戶" });
    } catch (caught) {
      if (caught instanceof ApiError && caught.status === 409) setFieldErrors({ username: caught.message });
      else setError(errorMessage(caught));
      setPending(false);
    }
  }

  return (
    <form onSubmit={submit} className="space-y-4" noValidate data-testid="register-form">
      <Field
        id={`${id}-username`}
        label="帳號"
        autoComplete="username"
        autoCapitalize="none"
        spellCheck={false}
        value={values.username}
        onChange={(event) => update("username", event.target.value)}
        onBlur={() => values.username && setFieldErrors((current) => ({ ...current, username: validateUsername(values.username) ?? undefined }))}
        error={fieldErrors.username}
        hint="3–30 個英文字母、數字或底線，不分大小寫"
        autoFocus
      />
      <Field
        id={`${id}-display-name`}
        label="顯示名稱（選填）"
        autoComplete="nickname"
        maxLength={50}
        value={values.displayName}
        onChange={(event) => update("displayName", event.target.value)}
        hint="留空時使用帳號"
      />
      <Field
        id={`${id}-password`}
        label="密碼"
        type="password"
        autoComplete="new-password"
        value={values.password}
        onChange={(event) => update("password", event.target.value)}
        error={fieldErrors.password}
        hint="至少 8 個字元"
      />
      <Field
        id={`${id}-confirm`}
        label="確認密碼"
        type="password"
        autoComplete="new-password"
        value={values.confirm}
        onChange={(event) => update("confirm", event.target.value)}
        error={fieldErrors.confirm}
      />
      <FormError message={error} />
      <Button type="submit" className="w-full" disabled={pending}>
        {pending ? <LoaderCircle className="animate-spin" /> : <UserPlus />}
        註冊並登入
      </Button>
    </form>
  );
}

export function AuthView() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user } = useAuth();
  const mode: AuthMode = searchParams.get("mode") === "register" ? "register" : "login";
  const next = safeNextPath(searchParams.get("next"));

  // 已登入（包含剛完成登入或註冊）就回到原本要去的頁面
  useEffect(() => {
    if (user) router.replace(next);
  }, [user, next, router]);

  function switchMode(value: string) {
    const params = new URLSearchParams(searchParams.toString());
    if (value === "register") params.set("mode", "register");
    else params.delete("mode");
    const search = params.toString();
    router.replace(search ? `/login?${search}` : "/login", { scroll: false });
  }

  if (user) {
    return (
      <p className="py-16 text-center text-sm text-muted-foreground" role="status">
        已登入為 {user.display_name}，正在前往頁面…
      </p>
    );
  }

  return (
    <div className="mx-auto w-full max-w-md py-4 sm:py-10">
      <Card className="gap-5">
        <CardHeader>
          <CardTitle className="text-xl">{mode === "register" ? "建立 StockVision 帳號" : "登入 StockVision"}</CardTitle>
          <CardDescription>
            {mode === "register"
              ? "每個帳號都有自己的 NT$1,000,000 模擬資金、自選股與價格提醒，彼此互不影響。"
              : "登入後即可使用模擬下單、投資組合、自選股與價格提醒。"}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          <Tabs value={mode} onValueChange={switchMode}>
            <TabsList className="grid w-full grid-cols-2" aria-label="登入或註冊">
              <TabsTrigger value="login">登入</TabsTrigger>
              <TabsTrigger value="register">註冊</TabsTrigger>
            </TabsList>
          </Tabs>
          {mode === "register" ? <RegisterForm key="register" /> : <LoginForm key="login" />}
          <p className="flex gap-2 text-xs leading-relaxed text-muted-foreground">
            <ShieldCheck className="mt-0.5 size-3.5 shrink-0" aria-hidden />
            密碼以 scrypt 加鹽雜湊保存在本機 SQLite；登入狀態存放在 HttpOnly Cookie，預設 7 天內不需重新登入。股票看盤、比較與大盤總覽不登入也能使用。
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
