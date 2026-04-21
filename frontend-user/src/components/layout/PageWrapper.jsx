import { motion } from "framer-motion";
import { pageTransition } from "../../animations/variants";

export function PageWrapper({ children, className = "" }) {
  return (
    <motion.main
      initial={pageTransition.initial}
      animate={pageTransition.animate}
      exit={pageTransition.exit}
      className={`min-h-screen bg-base bg-grid pt-[88px] ${className}`}
    >
      <div className="mx-auto w-full max-w-[1280px] px-6 pb-16">{children}</div>
    </motion.main>
  );
}

