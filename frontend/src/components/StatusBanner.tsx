import type { ReactNode } from "react";

interface StatusBannerProps {
  tone: "error" | "success" | "info";
  children: ReactNode;
}

export function StatusBanner({
  tone,
  children,
}: StatusBannerProps) {
  return (
    <div
      className={`status-banner status-banner--${tone}`}
      role={tone === "error" ? "alert" : "status"}
    >
      {children}
    </div>
  );
}