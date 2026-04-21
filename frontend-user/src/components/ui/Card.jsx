import { cn } from "../../utils/cn";

export function Card({ className, children, ...props }) {
  return (
    <div
      className={cn("card rounded-xl border border-[var(--border-subtle)] bg-surface p-4", className)}
      {...props}
    >
      {children}
    </div>
  );
}

