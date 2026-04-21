import { motion } from "framer-motion";
import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, ResponsiveContainer } from "recharts";
import { getHousingUnit } from "../api/housing";
import { getRecommendations, refreshRecommendations } from "../api/recommendations";
import { staggerContainer } from "../animations/variants";
import { PageWrapper } from "../components/layout/PageWrapper";
import { ListingCard } from "../components/shared/ListingCard";
import { Button } from "../components/ui/Button";
import { ErrorState } from "../components/ui/ErrorState";
import { Modal } from "../components/ui/Modal";
import { Skeleton } from "../components/ui/Skeleton";
import { useAuthStore } from "../store/authStore";

function buildRadarData(reasoning) {
  const items = Array.isArray(reasoning?.top_dimensions) ? reasoning.top_dimensions : [];
  if (!items.length) {
    return [
      { key: "Budget fit", value: 70 },
      { key: "Location", value: 70 },
      { key: "Amenities", value: 70 },
    ];
  }
  return items.slice(0, 5).map((row) => ({
    key: String(row.dimension || "Factor"),
    value: Math.max(1, Math.min(100, Math.round(Number(row.contribution || 0) * 100))),
  }));
}

export default function RecommendationsPage() {
  const user = useAuthStore((state) => state.user);
  const [selected, setSelected] = useState(null);

  const query = useQuery({
    queryKey: ["recommendations", user?.id],
    enabled: Boolean(user?.id),
    queryFn: async () => {
      try {
        await refreshRecommendations(user.id, { top_n: 12 });
      } catch {
        // Keep page functional even if refresh fails; fall back to latest saved results.
      }
      const rows = await getRecommendations(user.id);
      const list = Array.isArray(rows) ? rows : rows?.results || [];
      const merged = await Promise.all(
        list.map(async (item) => {
          try {
            const details = await getHousingUnit(item.unit_id);
            return {
              ...details,
              unit_id: item.unit_id,
              match: `${Math.round(Number(item.similarity_score || 0) * 100)}% match`,
              score: Number(item.similarity_score || 0),
              reasoning: item.reasoning_json || {},
              why: (item.reasoning_json?.top_dimensions || []).slice(0, 3).map((d) => d.dimension),
            };
          } catch {
            return {
              id: item.unit_id,
              unit_id: item.unit_id,
              title: `Housing ${item.unit_id}`,
              location: "N/A",
              match: `${Math.round(Number(item.similarity_score || 0) * 100)}% match`,
              score: Number(item.similarity_score || 0),
              reasoning: item.reasoning_json || {},
              why: (item.reasoning_json?.top_dimensions || []).slice(0, 3).map((d) => d.dimension),
            };
          }
        })
      );
      return merged;
    },
  });

  const recommendations = Array.isArray(query.data) ? query.data : [];
  const radarData = useMemo(() => buildRadarData(selected?.reasoning), [selected]);

  return (
    <PageWrapper className="space-y-6">
      <section className="relative overflow-hidden rounded-2xl border border-[var(--border-subtle)] p-8">
        <div className="absolute inset-0 bg-gradient-to-r from-primary/30 via-teal/20 to-transparent blur-2xl" style={{ animation: "meshMove 14s ease-in-out infinite" }} />
        <h1 className="relative font-display text-4xl font-extrabold">Recommended for You</h1>
        <p className="relative mt-2 text-[var(--text-secondary)]">Results are generated from your profile and housing preferences.</p>
        <Button className="relative mt-4" variant="outline" onClick={() => query.refetch()} disabled={query.isFetching}>
          {query.isFetching ? "Refreshing..." : "Refresh"}
        </Button>
      </section>

      {query.isLoading ? (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-[320px]" />
          ))}
        </div>
      ) : query.isError ? (
        <ErrorState message="Unable to load recommendations." onRetry={() => query.refetch()} />
      ) : recommendations.length === 0 ? (
        <div className="rounded-xl border border-[var(--border-subtle)] bg-surface p-6 text-[var(--text-secondary)]">
          No recommendations yet. Complete your profile and preferences, then refresh.
        </div>
      ) : (
        <motion.div variants={staggerContainer} initial="hidden" animate="visible" className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {recommendations.map((item) => (
            <div key={item.id || item.unit_id} className="rounded-xl border border-primary/40">
              <ListingCard listing={item} showScore onWhyMatched={setSelected} />
            </div>
          ))}
        </motion.div>
      )}

      <Modal open={Boolean(selected)} onClose={() => setSelected(null)}>
        <h3 className="font-display text-2xl">Why matched?</h3>
        <div className="mt-4 h-64">
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart data={radarData}>
              <PolarGrid />
              <PolarAngleAxis dataKey="key" stroke="#8B90A7" />
              <Radar dataKey="value" stroke="#6C63FF" fill="#6C63FF" fillOpacity={0.45} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </Modal>
    </PageWrapper>
  );
}
