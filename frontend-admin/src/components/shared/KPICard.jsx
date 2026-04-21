import CountUp from "react-countup";

export function KPICard({ icon, value, label, delta, accent = "var(--accent-primary)" }) {
  const positive = String(delta || "").trim().startsWith("+");
  return (
    <div className="rounded-[10px] border border-[var(--table-border)] bg-elevated p-4" style={{ borderLeft: `3px solid ${accent}` }}>
      <div className="mb-2 inline-flex h-8 w-8 items-center justify-center rounded-full" style={{ background: `${accent}22`, color: accent }}>
        {icon}
      </div>
      <p className="font-mono text-3xl font-bold">
        <CountUp end={Number(value || 0)} duration={0.8} separator="," />
      </p>
      <p className="text-xs text-[var(--text-secondary)]">{label}</p>
      <p className={`mt-2 text-xs ${positive ? "text-emerald" : "text-danger"}`}>{delta}</p>
    </div>
  );
}

