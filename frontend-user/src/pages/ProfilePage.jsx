import { useMutation, useQuery } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import { getProfileMetadata, getUserProfile, updateUserProfile } from "../api/user";
import { PageWrapper } from "../components/layout/PageWrapper";
import { Button } from "../components/ui/Button";
import { ErrorState } from "../components/ui/ErrorState";
import { FloatingInput } from "../components/ui/FloatingInput";
import { Skeleton } from "../components/ui/Skeleton";
import { useAuthStore } from "../store/authStore";

const tabs = ["Personal Info", "Housing Preferences", "Lifestyle", "Security", "Notifications"];

export default function ProfilePage() {
  const user = useAuthStore((state) => state.user);
  const userId = user?.id ?? user?.user_id;
  const [tab, setTab] = useState("Personal Info");
  const [saving, setSaving] = useState("idle");

  const profileQuery = useQuery({
    queryKey: ["profile", userId],
    queryFn: () => getUserProfile(userId),
    enabled: Boolean(userId),
  });

  const metadataQuery = useQuery({
    queryKey: ["profile-metadata"],
    queryFn: getProfileMetadata,
  });

  const universities = Array.isArray(metadataQuery.data?.universities) ? metadataQuery.data.universities : [];

  const profile = profileQuery.data || {};
  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    phone: "",
    bio: "",
    university: "",
    governorate: "",
  });

  const selectedUniversity = useMemo(
    () => universities.find((item) => item.name === form.university) || null,
    [universities, form.university]
  );

  useEffect(() => {
    if (!profileQuery.data) return;
    setForm({
      first_name: profile.first_name || "",
      last_name: profile.last_name || "",
      phone: profile.phone || "",
      bio: profile.bio || "",
      university: profile.university || "",
      governorate: profile.governorate || "",
    });
  }, [profileQuery.data, profile.first_name, profile.last_name, profile.phone, profile.bio, profile.university, profile.governorate]);

  useEffect(() => {
    if (!selectedUniversity) return;
    setForm((prev) => ({ ...prev, governorate: selectedUniversity.governorate || "" }));
  }, [selectedUniversity]);

  const saveMutation = useMutation({
    mutationFn: (payload) => updateUserProfile(userId, payload),
    onMutate: () => setSaving("loading"),
    onSuccess: () => {
      setSaving("saved");
      setTimeout(() => setSaving("idle"), 1200);
      profileQuery.refetch();
    },
    onError: () => setSaving("idle"),
  });

  const submit = (event) => {
    event.preventDefault();
    if (!userId) return;
    saveMutation.mutate(form);
  };

  return (
    <PageWrapper className="space-y-5">
      <section className="relative overflow-hidden rounded-2xl border border-[var(--border-subtle)] bg-surface">
        <div className="h-36 bg-gradient-to-r from-primary/50 to-teal/40" />
        <div className="relative pb-6 text-center">
          <div className="mx-auto -mt-12 flex h-24 w-24 items-center justify-center rounded-full border-4 border-base bg-elevated text-2xl">
            {(user?.email || "NU").slice(0, 2).toUpperCase()}
          </div>
          <p className="mt-2 font-display text-3xl font-bold">{`${profile.first_name || ""} ${profile.last_name || ""}`.trim() || "Student User"}</p>
          <p className="text-[var(--text-secondary)]">{profile.university || "University"} - {profile.governorate || "Governorate"}</p>
          <Button className="absolute right-4 top-4">Edit Profile</Button>
        </div>
      </section>

      <div className="flex flex-wrap gap-2">
        {tabs.map((item) => (
          <Button key={item} variant={tab === item ? "primary" : "outline"} onClick={() => setTab(item)}>
            {item}
          </Button>
        ))}
      </div>

      {profileQuery.isLoading ? (
        <Skeleton className="h-[320px]" />
      ) : profileQuery.isError ? (
        <ErrorState message="Unable to load profile." onRetry={() => profileQuery.refetch()} />
      ) : (
        <form onSubmit={submit} className="space-y-4 rounded-xl border border-[var(--border-subtle)] bg-surface p-5">
          {tab === "Personal Info" ? (
            <>
              <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                <FloatingInput label="First Name" value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })} />
                <FloatingInput label="Last Name" value={form.last_name} onChange={(e) => setForm({ ...form, last_name: e.target.value })} />
              </div>
              <FloatingInput label="Email" type="email" value={user?.email || ""} disabled />
              <FloatingInput label="Phone" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
              <div>
                <p className="mb-1 text-xs text-[var(--text-secondary)]">University</p>
                <select
                  className="w-full rounded-xl border border-[var(--border-subtle)] bg-elevated px-3 py-3 text-sm"
                  value={form.university}
                  onChange={(e) => setForm({ ...form, university: e.target.value })}
                >
                  <option value="">Select University</option>
                  {universities.map((item) => (
                    <option key={item.name} value={item.name}>
                      {item.name}
                    </option>
                  ))}
                </select>
              </div>
              <FloatingInput label="Governorate" value={form.governorate} disabled />
              <FloatingInput label="Bio" value={form.bio} onChange={(e) => setForm({ ...form, bio: e.target.value })} />
            </>
          ) : null}

          {tab !== "Personal Info" ? (
            <div className="rounded-xl border border-[var(--border-subtle)] bg-elevated p-4 text-sm text-[var(--text-secondary)]">
              This section remains unchanged.
            </div>
          ) : null}

          <Button type="submit" className="mt-2 min-w-[140px]">
            {saving === "loading" ? "Saving..." : saving === "saved" ? "Saved" : "Save"}
          </Button>
        </form>
      )}
    </PageWrapper>
  );
}
