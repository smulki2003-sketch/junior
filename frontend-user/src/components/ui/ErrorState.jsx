import { Button } from "./Button";

export function ErrorState({ message, onRetry }) {
  return (
    <div className="rounded-xl border border-coral/40 bg-coral/10 p-5">
      <p className="mb-3 text-sm text-coral">⚠ {message || "Something went wrong."}</p>
      <Button variant="outline" onClick={onRetry}>
        Retry
      </Button>
    </div>
  );
}

