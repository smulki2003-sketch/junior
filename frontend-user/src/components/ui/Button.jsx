import { cn } from "../../utils/cn";

export function Button({ className, variant = "primary", children, ...props }) {
  const variants = {
    primary: "btn-primary text-white",
    outline: "bg-transparent border border-[var(--border-subtle)] text-[var(--text-primary)]",
    ghost: "bg-transparent text-[var(--text-secondary)] hover:text-[var(--text-primary)]",
    coral: "bg-coral text-white",
    teal: "bg-teal text-black",
  };

  return (
    <button
      className={cn(
        "inline-flex items-center justify-center rounded-xl px-4 py-2 text-sm font-medium transition",
        variants[variant],
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
}

