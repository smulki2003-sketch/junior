import { useId } from "react";

export function Input({ label, className = "", ...props }) {
  const id = useId();
  return (
    <div className={`relative ${className}`}>
      <input id={id} placeholder=" " className="floating-input" {...props} />
      <label htmlFor={id} className="floating-label">
        {label}
      </label>
    </div>
  );
}

