"use client";

import { Toaster as Sonner, type ToasterProps } from "sonner";

// 全站固定深色主題，因此直接指定 theme="dark"，不需要 next-themes
const Toaster = ({ ...props }: ToasterProps) => {
  return (
    <Sonner
      theme="dark"
      className="toaster group"
      style={
        {
          "--normal-bg": "var(--popover)",
          "--normal-text": "var(--popover-foreground)",
          "--normal-border": "var(--border)",
        } as React.CSSProperties
      }
      {...props}
    />
  );
};

export { Toaster };
