import { cn } from "../../utils/cn";

const variants = {
  primary: "bg-blue text-white",
  outline: "border border-[var(--border-subtle)] bg-transparent text-[var(--text-primary)]",
  danger: "bg-danger text-white",
  success: "bg-emerald text-black",
  ghost: "bg-transparent text-[var(--text-secondary)] hover:text-[var(--text-primary)]",
  cyan: "border border-cyan text-cyan bg-transparent",
};

export function Button({ className, variant = "primary", children, ...props }) {
  return (
    <button
      type={props.type || "button"}
      className={cn("inline-flex items-center justify-center rounded-md px-3 py-2 text-sm font-medium transition", variants[variant], className)}
      {...props}
    >
      {children}
    </button>
  );
}
