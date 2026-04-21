import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export function SimpleBarChart({ data, barKey = "value", color = "#3B82F6", layout = "vertical" }) {
  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout={layout}>
          <CartesianGrid strokeDasharray="2 6" stroke="rgba(255,255,255,0.06)" />
          {layout === "vertical" ? (
            <>
              <XAxis type="number" stroke="#7A8099" />
              <YAxis dataKey="label" type="category" stroke="#7A8099" width={120} />
            </>
          ) : (
            <>
              <XAxis dataKey="label" stroke="#7A8099" />
              <YAxis stroke="#7A8099" />
            </>
          )}
          <Tooltip contentStyle={{ background: "#161B27", border: "1px solid rgba(255,255,255,0.08)" }} />
          <Bar dataKey={barKey} fill={color} radius={[4, 4, 4, 4]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

