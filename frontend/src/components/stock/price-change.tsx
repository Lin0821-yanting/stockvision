import { TONE_ARROW, TONE_LABEL, TONE_TEXT_CLASS, formatPercent, formatSignedNumber, toneOf } from "@/lib/format";
import { cn } from "@/lib/utils";

/** 漲跌金額與漲跌幅：顏色＋▲▼＋正負號三重標示，不只靠顏色區分 */
export function PriceChange({
  change,
  changePct,
  className,
  hideAmount = false,
}: {
  change: number | null | undefined;
  changePct: number | null | undefined;
  className?: string;
  hideAmount?: boolean;
}) {
  const tone = toneOf(change ?? changePct);
  if (change == null && changePct == null) {
    return <span className={cn("text-muted-foreground", className)}>—</span>;
  }
  return (
    <span className={cn("inline-flex items-center gap-1 font-medium tabular whitespace-nowrap", TONE_TEXT_CLASS[tone], className)}>
      <span aria-hidden className="text-[0.75em]">
        {TONE_ARROW[tone]}
      </span>
      <span className="sr-only">{TONE_LABEL[tone]}</span>
      {!hideAmount && change != null ? <span>{formatSignedNumber(change)}</span> : null}
      {changePct != null ? <span>{hideAmount ? formatPercent(changePct) : `(${formatPercent(changePct)})`}</span> : null}
    </span>
  );
}
