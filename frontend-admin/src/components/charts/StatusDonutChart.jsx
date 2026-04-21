import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

const colors = ["#10B981", "#F59E0B", "#EF4444"];

export function StatusDonutChart({ data }) {
  const total = data.reduce((acc, item) => acc + Number(item.value || 0), 0);
  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie data={data} dataKey="value" nameKey="name" innerRadius={65} outerRadius={95}>
            {data.map((entry, index) => (
              <Cell key={entry.name} fill={colors[index % colors.length]} />
            ))}
          </Pie>
          <Tooltip contentStyle={{ background: "#161B27", border: "1px solid rgba(255,255,255,0.08)" }} />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
      <p className="-mt-8 text-center font-mono text-sm text-[var(--text-secondary)]">Total: {total}</p>
    </div>
  );
}

