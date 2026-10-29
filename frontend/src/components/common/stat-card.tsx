import { Card, CardContent } from "@/components/ui/card";
import { TONE_ARROW, TONE_LABEL, TONE_TEXT_CLASS, type Tone } from "@/lib/format";
import { cn } from "@/lib/utils";

/** 指標卡：標籤 · 數值（比例字寬）· 帶正負號的變化（顏色＋箭頭） */
export function StatCard({
  label,
  value,
  delta,
  tone = "flat",
  hint,
  valueClassName,
  testId,
}: {
  label: string;
  value: React.ReactNode;
  delta?: React.ReactNode;
  tone?: Tone;
  hint?: React.ReactNode;
  valueClassName?: string;
  testId?: string;
}) {
  return (
    <Card className="gap-0 py-4" data-testid={testId}>
      <CardContent className="px-4">
        <p className="text-xs text-muted-foreground">{label}</p>
        <p
          className={cn("mt-1 truncate text-base font-semibold tracking-tight sm:text-xl lg:text-2xl", valueClassName)}
          title={typeof value === "string" ? value : undefined}
        >
          {value}
        </p>
        {delta != null ? (
          <p className={cn("mt-0.5 text-xs font-medium", TONE_TEXT_CLASS[tone])}>
            <span aria-hidden>{TONE_ARROW[tone]} </span>
            <span className="sr-only">{TONE_LABEL[tone]}</span>
            {delta}
          </p>
        ) : null}
        {hint ? <p className="mt-1 text-xs text-muted-foreground">{hint}</p> : null}
      </CardContent>
    </Card>
  );
}
