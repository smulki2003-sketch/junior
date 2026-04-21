import { cn } from "../../utils/cn";

const toneClasses = {
  primary: "bg-primary/20 text-primary",
  coral: "bg-coral/20 text-coral",
  teal: "bg-teal/20 text-teal",
  amber: "bg-amber/20 text-amber",
  muted: "bg-white/5 text-[var(--text-secondary)]",
};

export function Badge({ tone = "muted", className, children }) {
  return (
    <span className={cn("rounded-full px-3 py-1 text-xs font-medium", toneClasses[tone], className)}>
      {children}
    </span>
  );
}

