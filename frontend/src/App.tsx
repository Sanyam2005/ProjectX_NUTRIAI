import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";

import { AppShell } from "@/components/layout/AppShell";
import { useAuth } from "@/contexts/AuthContext";
import { LandingPage } from "@/pages/Landing";
import { LoginPage } from "@/pages/Login";
import { DashboardPage } from "@/pages/Dashboard";
import { MealUploadPage } from "@/pages/MealUpload";
import { AIAnalysisPage } from "@/pages/AIAnalysis";
import { MealResultPage } from "@/pages/MealResult";
import { MealHistoryPage } from "@/pages/MealHistory";
import { StatsPage } from "@/pages/Stats";
import { ChallengesPage } from "@/pages/Challenges";
import { GoalSettingsPage } from "@/pages/GoalSettings";
import { ProfilePage } from "@/pages/Profile";

function Protected({ children }: { children: JSX.Element }) {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

const pageVariants = {
  initial: { opacity: 0, y: 8 },
  enter:   { opacity: 1, y: 0, transition: { duration: 0.25, ease: [0.16, 1, 0.3, 1] } },
  exit:    { opacity: 0, y: -8, transition: { duration: 0.2 } },
};

function AnimatedOutlet({ children }: { children: JSX.Element }) {
  const loc = useLocation();
  return (
    <AnimatePresence mode="wait">
      <motion.div key={loc.pathname} variants={pageVariants} initial="initial" animate="enter" exit="exit">
        {children}
      </motion.div>
    </AnimatePresence>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/"      element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />

      <Route
        path="/app"
        element={
          <Protected>
            <AppShell />
          </Protected>
        }
      >
        <Route index             element={<AnimatedOutlet><DashboardPage /></AnimatedOutlet>} />
        <Route path="upload"     element={<AnimatedOutlet><MealUploadPage /></AnimatedOutlet>} />
        <Route path="analyzing" element={<AnimatedOutlet><AIAnalysisPage /></AnimatedOutlet>} />
        <Route path="result"     element={<AnimatedOutlet><MealResultPage /></AnimatedOutlet>} />
        <Route path="history"    element={<AnimatedOutlet><MealHistoryPage /></AnimatedOutlet>} />
        <Route path="analytics"  element={<AnimatedOutlet><StatsPage /></AnimatedOutlet>} />
        <Route path="calendar"   element={<AnimatedOutlet><StatsPage /></AnimatedOutlet>} />
        <Route path="challenges" element={<AnimatedOutlet><ChallengesPage /></AnimatedOutlet>} />
        <Route path="goals"      element={<AnimatedOutlet><GoalSettingsPage /></AnimatedOutlet>} />
        <Route path="profile"    element={<AnimatedOutlet><ProfilePage /></AnimatedOutlet>} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
