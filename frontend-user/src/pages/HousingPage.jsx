import "leaflet/dist/leaflet.css";
import { AnimatePresence, motion } from "framer-motion";
import { useMemo, useState } from "react";
import { MapContainer, Marker, Popup, TileLayer } from "react-leaflet";
import { staggerContainer } from "../animations/variants";
import { useI18n } from "../i18n/useI18n";
import { PageWrapper } from "../components/layout/PageWrapper";
import { ListingCard } from "../components/shared/ListingCard";
import { Button } from "../components/ui/Button";
import { ErrorState } from "../components/ui/ErrorState";
import { Skeleton } from "../components/ui/Skeleton";
import { useSearch } from "../hooks/useSearch";
import { useSearchStore } from "../store/searchStore";

const filterPills = [
  { label: "Studio", value: "studio" },
  { label: "1BR", value: "1br" },
  { label: "2BR", value: "2br" },
  { label: "Shared", value: "shared" },
];
const LOCATION_COORDINATES = {
  mazzeh: [33.4995, 36.2476],
  malki: [33.5134, 36.2903],
  aburommaneh: [33.5102, 36.2851],
  muhajreen: [33.5288, 36.2723],
  baramkeh: [33.5073, 36.2858],
  "ruken aldin": [33.5379, 36.2823],
  "rukun aldin": [33.5379, 36.2823],
  qassa: [33.5239, 36.3188],
  kfarsouseh: [33.4818, 36.2863],
  jafra: [33.4718, 36.2897],
  damascus: [33.5138, 36.2765],
};

function listingKey(listing, index) {
  return listing?.id ?? listing?.unit_id ?? `${listing?.title || "listing"}-${index}`;
}

export default function HousingPage() {
  const { query, setQuery, mode, setMode, searchQuery } = useSearch();
  const { filters, updateFilters, resetFilters } = useSearchStore();
  const [drawerOpen, setDrawerOpen] = useState(false);
  const { t, isRTL } = useI18n();

  const listings = useMemo(() => {
    if (Array.isArray(searchQuery.data)) return searchQuery.data;
    return searchQuery.data?.results || [];
  }, [searchQuery.data]);

  const mapListings = useMemo(() => {
    const source = listings.length
      ? listings
      : [{ id: 1, title: "Campus Studio", location: "Damascus City Center", lat: 33.5138, lng: 36.2765 }];

    return source.map((listing) => {
      if (typeof listing.lat === "number" && typeof listing.lng === "number") {
        return listing;
      }

      const normalizedLocation = String(listing.location || "")
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, " ")
        .trim();
      const matchedKey = Object.keys(LOCATION_COORDINATES).find((key) => normalizedLocation.includes(key));
      const [lat, lng] = matchedKey ? LOCATION_COORDINATES[matchedKey] : LOCATION_COORDINATES.damascus;
      return { ...listing, lat, lng };
    });
  }, [listings]);

  return (
    <PageWrapper>
      <section className="sticky top-[76px] z-20 space-y-3 rounded-2xl border border-[var(--border-subtle)] bg-surface/90 p-4 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={t("housing.searchPlaceholder", "Search by location, university, or keyword...")}
            className="h-12 flex-1 rounded-full border border-[var(--border-subtle)] bg-elevated px-5"
          />
          <Button variant="outline" className="rounded-full" onClick={() => setDrawerOpen(true)} aria-label={t("housing.filters", "Filters")}>
            Filters
          </Button>
        </div>
        <div className="flex flex-wrap gap-2">
          {filterPills.map((pill) => (
            <button
              key={pill.value}
              onClick={() => updateFilters({ unit_type: pill.value })}
              className={`rounded-full border px-3 py-1 text-xs transition ${
                filters.unit_type === pill.value ? "scale-105 border-primary bg-primary text-white" : "border-[var(--border-subtle)]"
              }`}
            >
              {pill.label}
            </button>
          ))}
        </div>
      </section>

      <div className="mt-6 flex justify-end gap-2">
        <Button variant={mode === "map" ? "primary" : "outline"} onClick={() => setMode("map")}>
          Map
        </Button>
        <Button variant={mode === "list" ? "primary" : "outline"} onClick={() => setMode("list")}>
          List
        </Button>
      </div>

      {searchQuery.isLoading ? (
        <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-[300px]" />
          ))}
        </div>
      ) : searchQuery.isError ? (
        <div className="mt-6">
          <ErrorState message={t("common.error", "Unable to load listings.")} onRetry={() => searchQuery.refetch()} />
        </div>
      ) : mode === "map" ? (
        <div className="mt-6 overflow-hidden rounded-xl border border-[var(--border-subtle)]">
          <MapContainer center={[33.5138, 36.2765]} zoom={13} className="h-[560px] w-full">
            <TileLayer attribution="&copy; OpenStreetMap contributors" url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
            {mapListings.map((listing, index) => (
              <Marker key={listingKey(listing, index)} position={[listing.lat || 33.5138, listing.lng || 36.2765]}>
                <Popup>
                  <p>{listing.title}</p>
                </Popup>
              </Marker>
            ))}
          </MapContainer>
        </div>
      ) : listings.length === 0 ? (
        <div className="mt-10 rounded-xl border border-[var(--border-subtle)] bg-surface p-10 text-center">
          <p className="text-[var(--text-secondary)]">{t("housing.noResults", "No listings found for the current filters.")}</p>
        </div>
      ) : (
        <motion.div variants={staggerContainer} initial="hidden" animate="visible" className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {listings.map((listing, index) => (
            <ListingCard key={listingKey(listing, index)} listing={listing} />
          ))}
        </motion.div>
      )}

      <AnimatePresence>
        {drawerOpen ? (
          <motion.div
            className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setDrawerOpen(false)}
          >
            <motion.aside
              className={`glass absolute top-0 h-full w-[360px] p-6 ${isRTL ? "left-0 border-r border-[var(--border-subtle)]" : "right-0 border-l border-[var(--border-subtle)]"}`}
              initial={{ x: isRTL ? -380 : 380 }}
              animate={{ x: 0 }}
              exit={{ x: isRTL ? -380 : 380 }}
              onClick={(e) => e.stopPropagation()}
            >
              <h2 className="mb-4 font-display text-xl">{t("housing.filters", "Filters")}</h2>
              <div className="space-y-4">
                <div>
                  <p className="mb-2 text-sm">Price Range</p>
                  <input type="range" min={0} max={5000} value={filters.max_price} onChange={(e) => updateFilters({ max_price: Number(e.target.value) })} className="w-full accent-primary" />
                  <p className="mt-1 text-xs text-[var(--text-secondary)]">Max: ${filters.max_price}</p>
                </div>
                <div>
                  <p className="mb-2 text-sm">Minimum Stars</p>
                  <input type="range" min={1} max={5} step={0.5} value={filters.min_stars} onChange={(e) => updateFilters({ min_stars: Number(e.target.value) })} className="w-full accent-primary" />
                  <p className="mt-1 text-xs text-[var(--text-secondary)]">{filters.min_stars} / 5</p>
                </div>
                <div>
                  <p className="mb-2 text-sm">Minimum Workers</p>
                  <input type="range" min={1} max={10} value={filters.min_workers} onChange={(e) => updateFilters({ min_workers: Number(e.target.value) })} className="w-full accent-primary" />
                  <p className="mt-1 text-xs text-[var(--text-secondary)]">{filters.min_workers}</p>
                </div>
              </div>
              <div className="absolute bottom-6 left-6 right-6 space-y-2">
                <Button className="w-full" onClick={() => setDrawerOpen(false)}>
                  {t("housing.applyFilters", "Apply Filters")}
                </Button>
                <Button variant="ghost" className="w-full" onClick={resetFilters}>
                  {t("housing.resetFilters", "Reset")}
                </Button>
              </div>
            </motion.aside>
          </motion.div>
        ) : null}
      </AnimatePresence>
    </PageWrapper>
  );
}
