import { Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../auth";
import { RoleDepartmentForm } from "../components/RoleDepartmentForm";

export function OnboardingPage() {
  const { user, departments, updateProfile, logout } = useAuth();
  const navigate = useNavigate();
  if (!user) return null;
  if (!user.needs_onboarding) return <Navigate to="/dashboard" replace />;

  return (
    <div className="login">
      <div className="card login-card">
        <h1>Welcome{user.full_name ? `, ${user.full_name.split(" ")[0]}` : ""}</h1>
        <p className="lead">Tell us where you work. Your role decides which data and charts you can see.</p>
        <RoleDepartmentForm
          departments={departments}
          user={user}
          submitLabel="Continue"
          onSubmit={async (values) => {
            await updateProfile(values);
            navigate("/dashboard", { replace: true });
          }}
        />
        <button className="btn link" onClick={() => void logout()}>
          Use a different account
        </button>
      </div>
    </div>
  );
}
