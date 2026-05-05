import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { loginRequest } from "../api/auth";
import { getProfileMetadata, updateHousingPreferences, updateUserProfile } from "../api/user";
import { Button } from "../components/ui/Button";
import { FloatingInput } from "../components/ui/FloatingInput";
import { useAuth } from "../hooks/useAuth";
import { useAuthStore } from "../store/authStore";

const lifestyles = ["Early Riser", "Night Owl", "Pet Friendly", "Quiet", "Social"];

function splitFullName(fullName) {
  const clean = String(fullName || "").trim();
  if (!clean) return { first_name: "", last_name: "" };
  const chunks = clean.split(/\s+/).filter(Boolean);
  if (chunks.length === 1) return { first_name: chunks[0], last_name: "" };
  return {
    first_name: chunks[0],
    last_name: chunks.slice(1).join(" "),
  };
}

export default function RegisterPage() {
  const [step, setStep] = useState(1);
  const [metadata, setMetadata] = useState({ governorates: [], universities: [] });
  const [form, setForm] = useState({
    full_name: "",
    email: "",
    password: "",
    confirmPassword: "",
    university: "",
    governorate: "",
    year: "",
    program: "",
    lifestyle: [],
    budget: 1200,
    moveIn: "",
  });
  const { registerMutation } = useAuth();
  const authStore = useAuthStore();
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const initialAuthHandled = useRef(false);
  const navigate = useNavigate();

  useEffect(() => {
    if (initialAuthHandled.current) return;
    initialAuthHandled.current = true;
    if (isAuthenticated) {
      authStore.logout();
    }
  }, [isAuthenticated, authStore]);

  useEffect(() => {
    let mounted = true;
    getProfileMetadata()
      .then((data) => {
        if (!mounted) return;
        setMetadata({
          governorates: Array.isArray(data?.governorates) ? data.governorates : [],
          universities: Array.isArray(data?.universities) ? data.universities : [],
        });
      })
      .catch(() => {
        if (!mounted) return;
        setMetadata({ governorates: [], universities: [] });
      });
    return () => {
      mounted = false;
    };
  }, []);

  const selectedUniversity = useMemo(
    () => metadata.universities.find((item) => item.name === form.university) || null,
    [metadata.universities, form.university]
  );

  useEffect(() => {
    if (!selectedUniversity) return;
    setForm((prev) => ({ ...prev, governorate: selectedUniversity.governorate || "" }));
  }, [selectedUniversity]);

  const nextStep = () => setStep((s) => Math.min(3, s + 1));
  const prevStep = () => setStep((s) => Math.max(1, s - 1));

  const submit = async () => {
    if (step !== 3) return;
    if (form.password !== form.confirmPassword) {
      toast.error("Password confirmation does not match.");
      return;
    }
    if (!form.university) {
      toast.error("Please select your university.");
      return;
    }

    try {
      const registerResult = await registerMutation.mutateAsync({
        email: form.email,
        password: form.password,
      });
      const userId = registerResult?.id;
      if (!userId) throw new Error("Missing user id from register response.");

      const loginResult = await loginRequest({
        email: form.email,
        password: form.password,
      });
      authStore.login({
        user: loginResult.user,
        accessToken: loginResult.tokens?.access_token || "",
        refreshToken: loginResult.tokens?.refresh_token || "",
      });

      const { first_name, last_name } = splitFullName(form.full_name);
      await updateUserProfile(userId, {
        first_name,
        last_name,
        phone: "",
        university: form.university,
        governorate: form.governorate,
        bio: "",
      });

      const budget = Number(form.budget || 0);
      await updateHousingPreferences(userId, {
        min_budget: Math.max(0, Math.round(budget * 0.75)),
        max_budget: Math.max(0, Math.round(budget * 1.25)),
        preferred_locations: form.governorate ? [form.governorate] : [],
        preferred_types: [],
        preferred_services: [],
      });

      toast.success("Registration successful");
      navigate("/housing");
    } catch (error) {
      toast.error(error?.response?.data?.error?.message || "Registration failed");
    }
  };

  return (
    <main className="min-h-screen bg-base">
      <div className="grid min-h-screen grid-cols-1 lg:grid-cols-2">
        <section className="relative hidden overflow-hidden bg-surface p-12 lg:block">
          <div className="absolute inset-0 bg-gradient-to-br from-primary/20 to-coral/20 blur-2xl" />
          <h1 className="relative mt-36 max-w-md font-display text-5xl font-extrabold leading-tight">
            Build your student housing profile.
          </h1>
          <p className="relative mt-4 max-w-md text-[var(--text-secondary)]">
            Match with places and people that fit your lifestyle.
          </p>
        </section>

        <section className="flex items-center justify-center px-6 py-12">
          <form className="w-full max-w-md space-y-5 overflow-hidden rounded-xl border border-[var(--border-subtle)] bg-surface p-6">
            <div className="h-1 w-full rounded bg-elevated">
              <motion.div className="h-full rounded bg-primary" animate={{ width: `${(step / 3) * 100}%` }} />
            </div>
            <div className="flex justify-center gap-2">
              {[1, 2, 3].map((item) => (
                <span key={item} className={`h-2 w-2 rounded-full ${item <= step ? "bg-primary" : "bg-elevated"}`} />
              ))}
            </div>
            <div>
              <p className="text-sm text-[var(--text-secondary)]">Already have an account?</p>
              <Link to="/login" className="text-sm text-primary">
                Sign in -&gt;
              </Link>
            </div>

            <AnimatePresence mode="wait">
              <motion.div
                key={step}
                initial={{ opacity: 0, x: 30 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -30 }}
                className="space-y-4"
              >
                {step === 1 ? (
                  <>
                    <FloatingInput label="Full Name" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} required />
                    <FloatingInput label="University Email" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
                    <FloatingInput label="Password" type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required />
                    <FloatingInput
                      label="Confirm Password"
                      type="password"
                      value={form.confirmPassword}
                      onChange={(e) => setForm({ ...form, confirmPassword: e.target.value })}
                      required
                    />
                  </>
                ) : null}

                {step === 2 ? (
                  <>
                    <div>
                      <p className="mb-1 text-xs text-[var(--text-secondary)]">University</p>
                      <select
                        className="w-full rounded-xl border border-[var(--border-subtle)] bg-elevated px-3 py-3 text-sm"
                        value={form.university}
                        onChange={(e) => setForm({ ...form, university: e.target.value })}
                        required
                      >
                        <option value="">Select University</option>
                        {metadata.universities.map((item) => (
                          <option key={item.name} value={item.name}>
                            {item.name}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <p className="mb-1 text-xs text-[var(--text-secondary)]">Governorate</p>
                      <input
                        className="w-full rounded-xl border border-[var(--border-subtle)] bg-elevated px-3 py-3 text-sm"
                        value={form.governorate}
                        readOnly
                        placeholder="Auto-selected from university"
                      />
                    </div>
                    <FloatingInput label="Year of Study" value={form.year} onChange={(e) => setForm({ ...form, year: e.target.value })} />
                    <FloatingInput label="Program / Major" value={form.program} onChange={(e) => setForm({ ...form, program: e.target.value })} />
                  </>
                ) : null}

                {step === 3 ? (
                  <>
                    <div className="flex flex-wrap gap-2">
                      {lifestyles.map((item) => {
                        const active = form.lifestyle.includes(item);
                        return (
                          <button
                            key={item}
                            type="button"
                            onClick={() =>
                              setForm((prev) => ({
                                ...prev,
                                lifestyle: active ? prev.lifestyle.filter((x) => x !== item) : [...prev.lifestyle, item],
                              }))
                            }
                            className={`rounded-full px-3 py-1 text-xs ${active ? "bg-primary text-white" : "border border-[var(--border-subtle)]"}`}
                          >
                            {item}
                          </button>
                        );
                      })}
                    </div>
                    <div>
                      <label className="mb-1 block text-xs text-[var(--text-secondary)]">Budget (${form.budget})</label>
                      <input type="range" min="300" max="3000" value={form.budget} onChange={(e) => setForm({ ...form, budget: Number(e.target.value) })} className="w-full accent-primary" />
                      <div className="mt-1 flex justify-between font-mono text-xs text-[var(--text-secondary)]">
                        <span>$300</span>
                        <span>$3000</span>
                      </div>
                    </div>
                    <FloatingInput label="Preferred Move-In Date" type="date" value={form.moveIn} onChange={(e) => setForm({ ...form, moveIn: e.target.value })} />
                  </>
                ) : null}
              </motion.div>
            </AnimatePresence>

            <div className="flex items-center justify-between gap-3">
              <Button type="button" variant="ghost" onClick={prevStep} disabled={step === 1}>
                &lt;- Back
              </Button>
              {step < 3 ? (
                <Button type="button" onClick={nextStep}>
                  Next -&gt;
                </Button>
              ) : (
                <Button type="button" onClick={submit} disabled={registerMutation.isPending}>
                  {registerMutation.isPending ? "Creating..." : "Create Account"}
                </Button>
              )}
            </div>
          </form>
        </section>
      </div>
    </main>
  );
}
