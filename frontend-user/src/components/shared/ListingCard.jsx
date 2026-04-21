import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { fadeUp } from "../../animations/variants";
import { Badge } from "../ui/Badge";

export function ListingCard({ listing, showScore = false, onWhyMatched }) {
  const listingId = listing?.id ?? listing?.unit_id ?? null;
  const numericId = Number.isFinite(Number(listingId)) ? Number(listingId) : 0;
  const badge = listing.badge || (numericId % 2 === 0 ? "Popular" : "New");
  const badgeTone = badge.includes("New") ? "coral" : "amber";
  const detailsHref = listingId != null ? `/housing/${listingId}` : "/housing";

  return (
    <motion.article variants={fadeUp} className="card overflow-hidden rounded-xl border border-[var(--border-subtle)] bg-surface">
      <div className="relative aspect-[16/10]">
        <img
          src={listing.image_url || "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?q=80&w=1200&auto=format&fit=crop"}
          alt={listing.title || "Listing image"}
          className="h-full w-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/70 to-transparent" />
        <Badge tone={badgeTone} className="absolute right-3 top-3">
          {badge}
        </Badge>
        <div className="absolute bottom-3 left-3 font-mono text-2xl font-semibold text-white">${listing.price || 950}/mo</div>
        {showScore ? (
          <div className="absolute left-3 top-3 rounded-full bg-gradient-to-r from-primary to-teal px-3 py-1 font-mono text-xs font-semibold">
            {listing.match || "94% match"}
          </div>
        ) : null}
      </div>
      <div className="space-y-3 p-4">
        <div>
          <h3 className="font-display text-lg font-semibold">{listing.title}</h3>
          <p className="text-sm text-[var(--text-secondary)]">{listing.location || "Near campus"}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          {(listing.amenities || ["Furnished", "WiFi", "Near campus"]).slice(0, 3).map((amenity, index) => (
            <Badge key={`${amenity}-${index}`}>{amenity}</Badge>
          ))}
        </div>
        {showScore ? (
          <div className="space-y-2">
            <div className="flex flex-wrap gap-2 text-xs">
              {(listing.why || ["In your budget", "Near CS dept.", "Quiet building"]).map((reason, index) => (
                <span key={`${reason}-${index}`} className="rounded-full bg-primary/10 px-2 py-1 text-primary">
                  {reason}
                </span>
              ))}
            </div>
            <button onClick={() => onWhyMatched?.(listing)} className="text-sm text-primary underline">
              Why matched?
            </button>
          </div>
        ) : null}
        <div className="flex items-center justify-between">
          <span className="text-amber">★★★★★ {listing.star_rating || listing.rating || "4.9"}</span>
          <span className="text-xs text-[var(--text-secondary)]">
            {listing.current_occupancy ?? 0}/{listing.max_occupancy ?? 1} occupied
          </span>
          <Link to={detailsHref} className="text-sm text-primary">
            View Details
          </Link>
        </div>
      </div>
    </motion.article>
  );
}
