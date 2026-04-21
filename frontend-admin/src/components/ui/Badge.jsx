import { cn } from "../../utils/cn";

export function Badge({ className, children, ...props }) {
  return (
    <span className={cn("inline-flex items-center rounded-full px-2 py-1 text-xs font-medium", className)} {...props}>
      {children}
    </span>
  );
}
