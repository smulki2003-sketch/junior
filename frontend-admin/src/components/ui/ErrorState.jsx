import { Button } from "./Button";

export function ErrorState({ message, onRetry }) {
  return (
    <div className="rounded-[10px] border border-danger/40 bg-danger/10 p-4">
      <p className="text-sm text-danger">⚠ {message}</p>
      <Button className="mt-3" variant="outline" onClick={onRetry}>
        Retry
      </Button>
    </div>
  );
}

