import "leaflet/dist/leaflet.css";
import { motion } from "framer-motion";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { MapContainer, Marker, Popup, TileLayer } from "react-leaflet";
import { useParams } from "react-router-dom";
import toast from "react-hot-toast";
import { scaleIn } from "../animations/variants";
import { PageWrapper } from "../components/layout/PageWrapper";
import { Button } from "../components/ui/Button";
import { ErrorState } from "../components/ui/ErrorState";
import { Modal } from "../components/ui/Modal";
import { Skeleton } from "../components/ui/Skeleton";
import { extractApiErrorMessage } from "../api/client";
import { createBooking } from "../api/bookings";
import { getHousingUnit } from "../api/housing";
import { createPaymentIntent, getPaymentBanks, simulatePaymentSuccess } from "../api/payments";
import { useAuthStore } from "../store/authStore";
import { formatPrice } from "../utils/format";

const LOCATION_COORDINATES = {
  mazzeh: [33.4995, 36.2476],
  malki: [33.5134, 36.2903],
  "abu rummaneh": [33.5102, 36.2851],
  "abu rommaneh": [33.5102, 36.2851],
  muhajreen: [33.5288, 36.2723],
  baramkeh: [33.5073, 36.2858],
  "ruken al din": [33.5379, 36.2823],
  "rukun aldin": [33.5379, 36.2823],
  qassa: [33.5239, 36.3188],
  kfarsouseh: [33.4818, 36.2863],
  jafra: [33.4718, 36.2897],
  "city center": [33.5138, 36.2765],
  "bab musalla": [33.5008, 36.3059],
  "bab msalla": [33.5008, 36.3059],
  damascus: [33.5138, 36.2765],
};

function resolveLocationCoordinates(location) {
  const raw = String(location || "").toLowerCase().trim();
  if (!raw) return LOCATION_COORDINATES.damascus;

  const normalized = raw.replace(/[^a-z0-9]+/g, " ").trim();
  const matchedKey = Object.keys(LOCATION_COORDINATES).find(
    (key) => raw.includes(key) || normalized.includes(key)
  );

  return matchedKey ? LOCATION_COORDINATES[matchedKey] : LOCATION_COORDINATES.damascus;
}

function normalizeDate(value) {
  if (!value) return null;
  const text = String(value).slice(0, 10);
  if (!/^\d{4}-\d{2}-\d{2}$/.test(text)) return null;
  return text;
}

function isRangeAvailable(slots, checkIn, checkOut) {
  const start = normalizeDate(checkIn);
  const end = normalizeDate(checkOut);
  if (!start || !end || start > end) return false;
  if (!Array.isArray(slots) || slots.length === 0) return true;
  return slots.some((slot) => {
    if (!slot || slot.status !== "available") return false;
    const slotStart = normalizeDate(slot.start_date);
    const slotEnd = normalizeDate(slot.end_date);
    if (!slotStart || !slotEnd) return false;
    return start >= slotStart && end <= slotEnd;
  });
}

export default function HousingDetailPage() {
  const { id } = useParams();
  const user = useAuthStore((state) => state.user);
  const [openLightbox, setOpenLightbox] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const [dates, setDates] = useState({ checkIn: "", checkOut: "" });
  const [guests, setGuests] = useState(1);
  const [favorites, setFavorites] = useState(false);
  const [payerBankName, setPayerBankName] = useState("");
  const [payerAccountNumber, setPayerAccountNumber] = useState("");

  const hasValidId = id != null && id !== "undefined" && id !== "null";

  const detailQuery = useQuery({
    queryKey: ["housing-detail", id],
    queryFn: () => getHousingUnit(id),
    enabled: hasValidId,
  });
  const banksQuery = useQuery({
    queryKey: ["payment-banks"],
    queryFn: getPaymentBanks,
  });
  const syrianBanks = Array.isArray(banksQuery.data?.banks) ? banksQuery.data.banks : [];

  const bookingMutation = useMutation({
    mutationFn: createBooking,
    onSuccess: async (booking) => {
      try {
        let paymentIntentId = booking?.payment_intent_id;
        if (!paymentIntentId) {
          const paymentIntent = await createPaymentIntent({
            booking_id: booking.id,
            user_id: booking.user_id,
            payer_bank_name: payerBankName,
            payer_account_number: payerAccountNumber,
            amount: booking.total_price,
          });
          paymentIntentId = paymentIntent?.payment_intent_id;
        }
        if (paymentIntentId) {
          await simulatePaymentSuccess(paymentIntentId);
        }
        toast.success("Booking created and payment completed");
      } catch {
        toast.error("Booking created, but payment failed");
      }
    },
    onError: (error) => {
      const message = extractApiErrorMessage(error);
      if (!message) toast.error("Booking failed");
    },
  });

  if (!hasValidId) {
    return (
      <PageWrapper className="space-y-6">
        <ErrorState message="Invalid listing id." />
      </PageWrapper>
    );
  }

  const listing = detailQuery.data || {};
  const nightlyPrice = Number(listing.price || 900);
  const total = useMemo(() => nightlyPrice * Math.max(1, guests), [nightlyPrice, guests]);
  const [lat, lng] = useMemo(() => resolveLocationCoordinates(listing.location), [listing.location]);
  const amenityNames = useMemo(() => {
    if (!Array.isArray(listing.amenities)) return [];
    return listing.amenities
      .map((amenity) => (typeof amenity === "string" ? amenity : amenity?.name))
      .filter(Boolean);
  }, [listing.amenities]);
  const availabilitySlots = Array.isArray(listing.availability_slots) ? listing.availability_slots : [];
  const firstAvailableStart = useMemo(() => {
    const starts = availabilitySlots
      .filter((slot) => slot?.status === "available" && normalizeDate(slot.start_date))
      .map((slot) => normalizeDate(slot.start_date))
      .filter(Boolean)
      .sort();
    return starts[0] || "";
  }, [availabilitySlots]);

  const doBooking = () => {
    if (!dates.checkIn || !dates.checkOut) {
      toast.error("Select check-in and check-out dates.");
      return;
    }
    if (!payerBankName.trim()) {
      toast.error("Select or enter your bank name.");
      return;
    }
    if (payerAccountNumber.trim().length < 6) {
      toast.error("Enter a valid account number.");
      return;
    }
    if (dates.checkIn > dates.checkOut) {
      toast.error("Check-out date must be after check-in date.");
      return;
    }
    if (!isRangeAvailable(availabilitySlots, dates.checkIn, dates.checkOut)) {
      toast.error("Selected dates are not available for this unit. Please choose different dates.");
      return;
    }

    const unitId = Number.isFinite(Number(listing.id)) ? Number(listing.id) : Number(id);
    if (!Number.isFinite(unitId)) {
      toast.error("Invalid unit id.");
      return;
    }

    bookingMutation.mutate({
      unit_id: unitId,
      start_date: dates.checkIn,
      end_date: dates.checkOut,
      total_price: total,
      payer_bank_name: payerBankName.trim(),
      payer_account_number: payerAccountNumber.trim(),
    });
  };

  const openLocationInMaps = () => {
    const locationLabel = listing.location || "Damascus";
    const url = `https://www.google.com/maps?q=${encodeURIComponent(`${locationLabel} ${lat},${lng}`)}`;
    window.open(url, "_blank", "noopener,noreferrer");
  };

  return (
    <PageWrapper className="space-y-6">
      {detailQuery.isLoading ? (
        <Skeleton className="h-[60vh]" />
      ) : detailQuery.isError ? (
        <ErrorState message="Unable to load listing details." onRetry={() => detailQuery.refetch()} />
      ) : (
        <>
          <section className="overflow-hidden rounded-xl">
            <div className="grid h-[60vh] grid-cols-1 gap-3 md:grid-cols-3">
              <img src={listing.images?.[0]?.image_url || "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?q=80&w=1200&auto=format&fit=crop"} alt={listing.title || "Listing image"} className="h-full w-full rounded-xl object-cover md:col-span-2" />
              <div className="grid grid-rows-2 gap-3">
                <img src={listing.images?.[1]?.image_url || "https://images.unsplash.com/photo-1493666438817-866a91353ca9?q=80&w=800&auto=format&fit=crop"} alt="Gallery" className="h-full w-full rounded-xl object-cover" />
                <img src={listing.images?.[2]?.image_url || "https://images.unsplash.com/photo-1484154218962-a197022b5858?q=80&w=800&auto=format&fit=crop"} alt="Gallery" className="h-full w-full rounded-xl object-cover" />
              </div>
            </div>
            <div className="-mt-14 flex justify-end pr-4">
              <Button variant="outline" onClick={() => setOpenLightbox(true)}>View all photos</Button>
            </div>
          </section>

          <section className="grid grid-cols-1 gap-6 md:grid-cols-3">
            <div className="space-y-5 md:col-span-2">
              <div>
                <h1 className="font-display text-4xl font-bold">{listing.title || "Luxury Student Studio"}</h1>
                <p className="text-[var(--text-secondary)]">{listing.location || "City Center"} · {listing.star_rating || "4.9"}/5</p>
              </div>
              <div className="flex flex-wrap gap-2">
                {(amenityNames.length ? amenityNames : ["Furnished", "WiFi", "Near campus"]).map((amenity) => (
                  <span key={amenity} className="rounded-full bg-elevated px-3 py-1 text-sm">{amenity}</span>
                ))}
              </div>
              <div className="rounded-xl border border-[var(--border-subtle)] bg-surface p-4">
                <h2 className="mb-2 font-display text-xl">About this space</h2>
                <p className="text-[var(--text-secondary)]">
                  {(listing.description || "Fully furnished residence close to campus with modern amenities and flexible lease terms.").slice(0, expanded ? 900 : 180)}
                </p>
                <button className="mt-2 text-sm text-primary" onClick={() => setExpanded((prev) => !prev)}>
                  {expanded ? "Show less" : "Show more"}
                </button>
              </div>
              <div className="rounded-xl border border-[var(--border-subtle)] bg-surface p-4">
                <div className="mb-3 flex items-center justify-between gap-3">
                  <h3 className="font-display text-lg">Location Preview</h3>
                  <Button variant="outline" onClick={openLocationInMaps}>Open Location</Button>
                </div>
                <div className="h-48 overflow-hidden rounded-xl border border-[var(--border-glow)] bg-elevated">
                  <MapContainer center={[lat, lng]} zoom={14} className="h-full w-full">
                    <TileLayer attribution="&copy; OpenStreetMap contributors" url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
                    <Marker position={[lat, lng]}>
                      <Popup>
                        <p>{listing.title || "Listing"}</p>
                        <p>{listing.location || "Damascus"}</p>
                      </Popup>
                    </Marker>
                  </MapContainer>
                </div>
              </div>
              <div className="space-y-3">
                <h3 className="font-display text-lg">Listing Details</h3>
                <div className="rounded-xl border border-[var(--border-subtle)] bg-surface p-3 text-sm text-[var(--text-secondary)]">
                  <p>Unit Type: {listing.unit_type || "-"}</p>
                  <p>Workers: {listing.worker_count ?? "-"}</p>
                  <p>Occupancy: {listing.current_occupancy ?? 0}/{listing.max_occupancy ?? 1}</p>
                </div>
              </div>
            </div>

            <motion.aside variants={scaleIn} initial="hidden" animate="visible" className="sticky top-[88px] h-fit rounded-xl border border-[var(--border-glow)] bg-elevated p-4">
              <p className="font-mono text-3xl font-bold text-primary">{formatPrice(nightlyPrice)}/mo</p>
              <div className="mt-4 space-y-3">
                <input
                  type="date"
                  value={dates.checkIn}
                  min={firstAvailableStart || undefined}
                  onChange={(e) => setDates((prev) => ({ ...prev, checkIn: e.target.value }))}
                  className="w-full rounded-lg border border-[var(--border-subtle)] bg-surface px-3 py-2"
                />
                <input
                  type="date"
                  value={dates.checkOut}
                  min={dates.checkIn || firstAvailableStart || undefined}
                  onChange={(e) => setDates((prev) => ({ ...prev, checkOut: e.target.value }))}
                  className="w-full rounded-lg border border-[var(--border-subtle)] bg-surface px-3 py-2"
                />
                <select
                  className="w-full rounded-lg border border-[var(--border-subtle)] bg-surface px-3 py-2"
                  value={payerBankName}
                  onChange={(e) => setPayerBankName(e.target.value)}
                >
                  <option value="">Select Syrian bank</option>
                  {syrianBanks.map((bank) => (
                    <option key={bank} value={bank}>
                      {bank}
                    </option>
                  ))}
                </select>
                <input
                  type="text"
                  value={payerAccountNumber}
                  onChange={(e) => setPayerAccountNumber(e.target.value)}
                  placeholder="Account number"
                  className="w-full rounded-lg border border-[var(--border-subtle)] bg-surface px-3 py-2"
                />
                <div className="flex items-center justify-between rounded-lg border border-[var(--border-subtle)] bg-surface px-3 py-2">
                  <span>Guests</span>
                  <div className="flex items-center gap-2">
                    <button onClick={() => setGuests((g) => Math.max(1, g - 1))}>-</button>
                    <span>{guests}</span>
                    <button onClick={() => setGuests((g) => g + 1)}>+</button>
                  </div>
                </div>
                <div className="rounded-lg bg-surface p-3 text-sm">
                  <p className="flex justify-between"><span>Rent</span><span>{formatPrice(nightlyPrice)}</span></p>
                  <p className="mt-1 flex justify-between"><span>Total</span><span className="font-mono">{formatPrice(total)}</span></p>
                </div>
                <Button className="w-full py-3" onClick={doBooking} disabled={bookingMutation.isPending}>
                  {bookingMutation.isPending ? "Processing payment..." : "Pay & Book Now"}
                </Button>
                <Button className="w-full" variant="outline" onClick={() => setFavorites((prev) => !prev)}>
                  {favorites ? "Favorited" : "Add to Favorites"}
                </Button>
                <div className="flex flex-wrap gap-2 text-xs">
                  <span className="rounded-full bg-teal/20 px-3 py-1 text-teal">Verified Listing</span>
                  <span className="rounded-full bg-primary/20 px-3 py-1 text-primary">Instant Booking</span>
                </div>
              </div>
            </motion.aside>
          </section>
        </>
      )}

      <Modal open={openLightbox} onClose={() => setOpenLightbox(false)}>
        <div className="space-y-3">
          <h3 className="font-display text-2xl">Photos</h3>
          <img src={listing.images?.[0]?.image_url || "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?q=80&w=1200&auto=format&fit=crop"} alt="Full gallery image" className="h-[60vh] w-full rounded-xl object-cover" />
        </div>
      </Modal>
    </PageWrapper>
  );
}
