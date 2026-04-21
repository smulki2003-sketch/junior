import { motion } from "framer-motion";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { Input } from "../../components/ui/Input";
import { Button } from "../../components/ui/Button";
import { useAdminAuth } from "../../hooks/useAdminAuth";

export default function AdminLoginPage() {
  const { loginMutation } = useAdminAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: "", password: "" });
  const [showPassword, setShowPassword] = useState(false);
  const [shake, setShake] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  async function onSubmit(event) {
    event.preventDefault();
    setErrorMessage("");
    try {
      await loginMutation.mutateAsync(form);
      toast.success("Signed in");
      navigate("/admin/dashboard");
    } catch (error) {
      setShake(true);
      setTimeout(() => setShake(false), 450);
      setErrorMessage(error?.response?.data?.error?.message || "Invalid admin credentials.");
    }
  }

  return (
    <main className="dot-grid relative flex min-h-screen items-center justify-center bg-base p-4">
      <div className="pointer-events-none absolute h-80 w-80 rounded-full bg-blue/10 blur-3xl" style={{ animation: "drift 12s ease-in-out infinite" }} />
      <motion.form
        onSubmit={onSubmit}
        initial={{ opacity: 0, scale: 0.96 }}
        animate={{ opacity: 1, scale: 1 }}
        className={`relative w-full max-w-[480px] rounded-xl border border-[var(--border-subtle)] bg-elevated p-6 shadow-xl ${
          shake ? "animate-[shake_0.4s_ease]" : ""
        }`}
      >
        <div className="mb-4 flex justify-center">
          <div className="inline-flex h-12 w-12 items-center justify-center rounded-full bg-blue/20 text-2xl text-blue">🛡️</div>
        </div>
        <h1 className="text-center font-display text-2xl font-bold">Admin Portal</h1>
        <div className="mx-auto mt-3 inline-flex w-full items-center justify-center rounded-full bg-amber/20 px-3 py-1 text-xs text-amber">
          🔒 Restricted Access — Authorized Personnel Only
        </div>
        <div className="mt-5 space-y-4">
          <Input
            label="Email"
            type="email"
            value={form.email}
            onChange={(e) => setForm((p) => ({ ...p, email: e.target.value }))}
            required
          />
          <div className="relative">
            <Input
              label="Password"
              type={showPassword ? "text" : "password"}
              value={form.password}
              onChange={(e) => setForm((p) => ({ ...p, password: e.target.value }))}
              required
            />
            <button type="button" className="absolute right-3 top-4 text-xs text-[var(--text-secondary)]" onClick={() => setShowPassword((v) => !v)}>
              {showPassword ? "Hide" : "Show"}
            </button>
          </div>
          {errorMessage ? <p className="text-sm text-danger">{errorMessage}</p> : null}
          <Button className="w-full py-2" type="submit" disabled={loginMutation.isPending}>
            {loginMutation.isPending ? "Signing In..." : "Sign In to Dashboard"}
          </Button>
        </div>
      </motion.form>
    </main>
  );
}

