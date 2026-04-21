import { Toaster } from "react-hot-toast";

export function ToastProvider() {
  return (
    <Toaster
      position="bottom-right"
      toastOptions={{
        style: {
          background: "var(--bg-elevated)",
          color: "var(--text-primary)",
          border: "1px solid var(--border-subtle)",
        },
        success: {
          style: { borderLeft: "4px solid var(--accent-teal)" },
        },
        error: {
          style: { borderLeft: "4px solid var(--accent-secondary)" },
        },
      }}
    />
  );
}

