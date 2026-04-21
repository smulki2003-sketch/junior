import { useId } from "react";

export function FloatingInput({ label, type = "text", className = "", ...props }) {
  const id = useId();
  return (
    <div className={`relative ${className}`}>
      <input id={id} type={type} placeholder=" " className="floating-input" {...props} />
      <label htmlFor={id} className="floating-label">
        {label}
      </label>
    </div>
  );
}

