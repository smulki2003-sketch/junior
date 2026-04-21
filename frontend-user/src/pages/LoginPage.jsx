import { motion } from "framer-motion";
import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { fadeUp, staggerContainer } from "../animations/variants";
import { Button } from "../components/ui/Button";
import { FloatingInput } from "../components/ui/FloatingInput";
import { useAuth } from "../hooks/useAuth";

export default function LoginPage() {
  const { loginMutation } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [showPassword, setShowPassword] = useState(false);
  const [form, setForm] = useState({ email: "", password: "" });

  const onSubmit = async (event) => {
    event.preventDefault();
    try {
      await loginMutation.mutateAsync(form);
      toast.success("Signed in successfully");
      navigate(location.state?.from || "/housing", { replace: true });
    } catch (error) {
      toast.error(error?.response?.data?.error?.message || "Sign in failed");
    }
  };

  return (
    <main className="min-h-screen bg-base">
      <div className="grid min-h-screen grid-cols-1 lg:grid-cols-2">
        <motion.section
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="relative hidden overflow-hidden bg-surface p-12 lg:block"
        >
          <motion.div variants={fadeUp} className="absolute left-1/2 top-1/2 h-72 w-72 -translate-x-1/2 -translate-y-1/2 rounded-[40%] bg-primary/50 blur-3xl" />
          <motion.div variants={fadeUp} className="absolute left-1/2 top-1/2 h-48 w-48 -translate-x-1/2 -translate-y-1/2 rounded-3xl border border-[var(--border-glow)] bg-elevated shadow-glow" />
          <motion.h1 variants={fadeUp} className="relative mt-36 max-w-md font-display text-5xl font-extrabold leading-tight">
            Find your perfect space.
          </motion.h1>
          <motion.p variants={fadeUp} className="relative mt-4 max-w-md text-[var(--text-secondary)]">
            Premium student housing search, booking, and matching in one place.
          </motion.p>
          <div className="pointer-events-none absolute inset-0">
            <div className="absolute left-24 top-28 rounded-full bg-elevated px-4 py-2 text-xs" style={{ animation: "orbit 12s linear infinite" }}>
              ⭐ 4.9 · Studio near campus
            </div>
            <div className="absolute right-24 top-56 rounded-full bg-elevated px-4 py-2 text-xs" style={{ animation: "orbit 15s linear infinite reverse" }}>
              ⚡ Instant booking
            </div>
          </div>
        </motion.section>

        <section className="flex items-center justify-center px-6 py-12">
          <motion.form
            initial={{ opacity: 0, x: 20, filter: "blur(8px)" }}
            animate={{ opacity: 1, x: 0, filter: "blur(0px)" }}
            onSubmit={onSubmit}
            className="w-full max-w-md space-y-5"
          >
            <div>
              <h2 className="font-display text-3xl font-bold">Welcome back</h2>
              <p className="mt-2 text-sm text-[var(--text-secondary)]">
                Don&apos;t have an account?{" "}
                <Link to="/register" className="text-primary">
                  Sign up →
                </Link>
              </p>
            </div>

            <FloatingInput
              label="University Email"
              type="email"
              value={form.email}
              onChange={(e) => setForm((prev) => ({ ...prev, email: e.target.value }))}
              required
            />
            <div className="relative">
              <FloatingInput
                label="Password"
                type={showPassword ? "text" : "password"}
                value={form.password}
                onChange={(e) => setForm((prev) => ({ ...prev, password: e.target.value }))}
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword((prev) => !prev)}
                className="absolute right-3 top-4 text-xs text-[var(--text-secondary)]"
              >
                {showPassword ? "Hide" : "Show"}
              </button>
            </div>
            <div className="text-right text-xs text-[var(--text-secondary)]">
              <button type="button">Forgot password?</button>
            </div>

            <Button className="w-full py-3" disabled={loginMutation.isPending}>
              {loginMutation.isPending ? "Signing In..." : "Sign In"}
            </Button>

            <div className="text-center text-sm text-[var(--text-secondary)]">— or continue with —</div>
            <div className="grid grid-cols-2 gap-3">
              <Button type="button" variant="outline">
                Google
              </Button>
              <Button type="button" variant="outline">
                GitHub
              </Button>
            </div>
          </motion.form>
        </section>
      </div>
    </main>
  );
}

