import type { ReactNode } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth";
import { Layout } from "./components/Layout";
import { DashboardPage } from "./pages/DashboardPage";
import { LoginPage } from "./pages/LoginPage";
import { OnboardingPage } from "./pages/OnboardingPage";
import { ProfilePage } from "./pages/ProfilePage";

/** Signed-in users only. Anyone without a role is sent to onboarding first. */
function RequireAuth({ children, allowUnonboarded = false }: { children: ReactNode; allowUnonboarded?: boolean }) {
  const { status, user } = useAuth();
  if (status === "loading") return <p className="splash">Loading...</p>;
  if (status === "anonymous" || !user) return <Navigate to="/login" replace />;
  if (user.needs_onboarding && !allowUnonboarded) return <Navigate to="/onboarding" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/onboarding"
        element={
          <RequireAuth allowUnonboarded>
            <OnboardingPage />
          </RequireAuth>
        }
      />
      <Route
        element={
          <RequireAuth>
            <Layout />
          </RequireAuth>
        }
      >
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/profile" element={<ProfilePage />} />
      </Route>
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
