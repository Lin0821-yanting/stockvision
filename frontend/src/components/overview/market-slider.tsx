"use client";

import { useRef, useState } from "react";

import { cn } from "@/lib/utils";
import { clampPage, DRAG_START_PX, dragOffset, swipeDirection } from "@/lib/swipe";

export type SliderPage = { id: string; label: string; content: React.ReactNode };

/** 上方的「台股｜美股」切換鈕：底色會滑到選取的那一邊 */
export function PageToggle({
  pages,
  index,
  onChange,
}: {
  pages: SliderPage[];
  index: number;
  onChange: (index: number) => void;
}) {
  function onKeyDown(event: React.KeyboardEvent) {
    const step = event.key === "ArrowRight" ? 1 : event.key === "ArrowLeft" ? -1 : 0;
    if (!step) return;
    event.preventDefault();
    const next = clampPage(index + step, pages.length);
    onChange(next);
    document.getElementById(`overview-tab-${pages[next].id}`)?.focus();
  }

  return (
    <div
      role="tablist"
      aria-label="選擇市場"
      className="relative grid rounded-lg bg-muted p-[3px]"
      style={{ gridTemplateColumns: `repeat(${pages.length}, minmax(0, 1fr))` }}
      onKeyDown={onKeyDown}
    >
      <span
        aria-hidden
        className="absolute inset-y-[3px] left-[3px] rounded-md bg-background shadow-sm transition-transform duration-300 ease-out motion-reduce:transition-none dark:bg-input/60"
        style={{ width: `calc((100% - 6px) / ${pages.length})`, transform: `translateX(${index * 100}%)` }}
      />
      {pages.map((page, position) => (
        <button
          key={page.id}
          id={`overview-tab-${page.id}`}
          type="button"
          role="tab"
          aria-selected={position === index}
          aria-controls={`overview-panel-${page.id}`}
          tabIndex={position === index ? 0 : -1}
          onClick={() => onChange(position)}
          className={cn(
            "relative z-10 rounded-md px-5 py-1 text-sm font-medium transition-colors outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50",
            position === index ? "text-foreground" : "text-muted-foreground hover:text-foreground",
          )}
        >
          {page.label}
        </button>
      ))}
    </div>
  );
}

/**
 * 左右滑動的視窗：觸控或滑鼠拖曳超過 60px 換頁，也可以用方向鍵或下方圓點切換。
 * touch-action: pan-y 讓上下捲動照常運作；沒有顯示的那一頁設為 inert，鍵盤焦點不會跑進去。
 */
export function MarketSlider({
  pages,
  index,
  onChange,
}: {
  pages: SliderPage[];
  index: number;
  onChange: (index: number) => void;
}) {
  const [offset, setOffset] = useState<number | null>(null);
  const start = useRef<{ x: number; y: number; pointer: number } | null>(null);
  const dragging = useRef(false);
  const suppressClick = useRef(false);

  function onPointerDown(event: React.PointerEvent<HTMLDivElement>) {
    if (event.pointerType === "mouse" && event.button !== 0) return;
    start.current = { x: event.clientX, y: event.clientY, pointer: event.pointerId };
    dragging.current = false;
    suppressClick.current = false;
  }

  function onPointerMove(event: React.PointerEvent<HTMLDivElement>) {
    const origin = start.current;
    if (!origin || origin.pointer !== event.pointerId) return;
    const dx = event.clientX - origin.x;
    const dy = event.clientY - origin.y;
    if (!dragging.current) {
      if (Math.abs(dy) > DRAG_START_PX && Math.abs(dy) >= Math.abs(dx)) {
        start.current = null; // 使用者在上下捲動
        return;
      }
      if (Math.abs(dx) < DRAG_START_PX) return;
      dragging.current = true;
      event.currentTarget.setPointerCapture(event.pointerId);
    }
    setOffset(dragOffset(dx, index, pages.length));
  }

  function onPointerUp(event: React.PointerEvent<HTMLDivElement>) {
    const origin = start.current;
    start.current = null;
    if (!origin || origin.pointer !== event.pointerId) return;
    if (dragging.current) {
      suppressClick.current = true; // 拖曳結束時不要觸發卡片連結
      const next = clampPage(index + swipeDirection(event.clientX - origin.x, event.clientY - origin.y), pages.length);
      if (next !== index) onChange(next);
    }
    dragging.current = false;
    setOffset(null);
  }

  function onPointerCancel() {
    start.current = null;
    dragging.current = false;
    setOffset(null);
  }

  function onClickCapture(event: React.MouseEvent) {
    if (!suppressClick.current) return;
    suppressClick.current = false;
    event.preventDefault();
    event.stopPropagation();
  }

  function onKeyDown(event: React.KeyboardEvent) {
    if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement) return;
    const step = event.key === "ArrowRight" ? 1 : event.key === "ArrowLeft" ? -1 : 0;
    if (!step) return;
    const next = clampPage(index + step, pages.length);
    if (next !== index) {
      event.preventDefault();
      onChange(next);
    }
  }

  const share = 100 / pages.length;
  return (
    <div className="space-y-3">
      <div
        role="region"
        aria-roledescription="輪播"
        aria-label="市場頁面，可左右滑動切換"
        className={cn("overflow-hidden", offset !== null && "cursor-grabbing select-none")}
        style={{ touchAction: "pan-y" }}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerCancel={onPointerCancel}
        onClickCapture={onClickCapture}
        onDragStart={(event) => event.preventDefault()}
        onKeyDown={onKeyDown}
        data-testid="market-slider"
        data-page={pages[index].id}
      >
        <div
          className={cn(
            "flex items-start",
            offset === null && "transition-transform duration-300 ease-out motion-reduce:transition-none",
          )}
          style={{
            width: `${pages.length * 100}%`,
            transform: `translateX(calc(${-index * share}% + ${offset ?? 0}px))`,
          }}
        >
          {pages.map((page, position) => (
            <section
              key={page.id}
              id={`overview-panel-${page.id}`}
              role="tabpanel"
              aria-labelledby={`overview-tab-${page.id}`}
              inert={position !== index}
              className="min-w-0 shrink-0 px-px"
              style={{ width: `${share}%` }}
            >
              {page.content}
            </section>
          ))}
        </div>
      </div>
      <div className="flex justify-center gap-2" aria-label="頁面">
        {pages.map((page, position) => (
          <button
            key={page.id}
            type="button"
            onClick={() => onChange(position)}
            aria-label={`第 ${position + 1} 頁：${page.label}`}
            aria-current={position === index ? "true" : undefined}
            className="flex size-6 items-center justify-center rounded-full outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50"
          >
            <span
              className={cn(
                "h-1.5 rounded-full transition-all duration-300 motion-reduce:transition-none",
                position === index ? "w-5 bg-primary" : "w-1.5 bg-muted-foreground/40",
              )}
            />
          </button>
        ))}
      </div>
      <p className="sr-only" aria-live="polite">
        目前顯示：{pages[index].label}
      </p>
    </div>
  );
}
