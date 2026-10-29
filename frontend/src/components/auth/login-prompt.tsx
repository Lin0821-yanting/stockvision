"use client";

import Link from "next/link";
import { LockKeyhole, LogIn, UserPlus, type LucideIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useLoginHref } from "@/hooks/use-login-href";
import { cn } from "@/lib/utils";

export function LoginButtons({ size = "sm", className }: { size?: "sm" | "default"; className?: string }) {
  const loginHref = useLoginHref("login");
  const registerHref = useLoginHref("register");
  return (
    <div className={cn("flex flex-wrap justify-center gap-2", className)}>
      <Button asChild size={size}>
        <Link href={loginHref}>
          <LogIn />
          登入
        </Link>
      </Button>
      <Button asChild size={size} variant="outline">
        <Link href={registerHref}>
          <UserPlus />
          免費註冊
        </Link>
      </Button>
    </div>
  );
}

/** 未登入時取代個人資料區塊的提示 */
export function LoginPrompt({
  title,
  description,
  icon: Icon = LockKeyhole,
  className,
}: {
  title: string;
  description?: React.ReactNode;
  icon?: LucideIcon;
  className?: string;
}) {
  return (
    <div
      className={cn("flex flex-col items-center justify-center gap-2 rounded-lg border border-dashed p-8 text-center", className)}
      data-testid="login-prompt"
    >
      <Icon className="size-8 text-muted-foreground" aria-hidden />
      <p className="font-medium">{title}</p>
      {description ? <p className="max-w-sm text-sm text-muted-foreground">{description}</p> : null}
      <LoginButtons className="mt-2" />
    </div>
  );
}

export function LoginPromptCard(props: React.ComponentProps<typeof LoginPrompt>) {
  return (
    <Card className="py-0">
      <CardContent className="p-0">
        <LoginPrompt {...props} className={cn("border-0 py-12", props.className)} />
      </CardContent>
    </Card>
  );
}
