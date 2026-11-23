import { useEffect, useRef, useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../auth";
import { getGoogleClientId } from "../config";
import { loadGoogle } from "../google";

export function LoginPage() {
  const { status, user, loginWithGoogle } = useAuth();
  const navigate = useNavigate();
  const buttonRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);
  const clientId = getGoogleClientId();

  useEffect(() => {
    if (!clientId) return;
    let cancelled = false;
    loadGoogle()
      .then((google) => {
        if (cancelled || !buttonRef.current) return;
        google.accounts.id.initialize({
          client_id: clientId,
          callback: ({ credential }) => {
            setError(null);
            loginWithGoogle(credential)
              .then((signedIn) => navigate(signedIn.needs_onboarding ? "/onboarding" : "/dashboard", { replace: true }))
              .catch((err: unknown) => setError(err instanceof Error ? err.message : "Sign-in failed."));
          },
        });
        google.accounts.id.renderButton(buttonRef.current, { theme: "outline", size: "large", text: "signin_with", width: 280 });
      })
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Could not load Google sign-in."));
    return () => {
      cancelled = true;
    };
  }, [clientId, loginWithGoogle, navigate]);

  if (status === "authenticated" && user) {
    return <Navigate to={user.needs_onboarding ? "/onboarding" : "/dashboard"} replace />;
  }

  return (
    <div className="login">
      <div className="card login-card">
        <h1>RoleCanvas</h1>
        <p className="lead">Role-aware dashboards. Sign in to see charts built for your role.</p>
        {clientId ? (
          <div ref={buttonRef} className="google-button" aria-label="Sign in with Google" />
        ) : (
          <p className="alert error" role="alert">
            Google sign-in is not configured. Set GOOGLE_OAUTH_CLIENT_ID in .env and restart the frontend.
          </p>
        )}
        {error && (
          <p className="alert error" role="alert">
            {error}
          </p>
        )}
        <p className="hint">Only your name, email and profile picture are used. No password is stored.</p>
      </div>
    </div>
  );
}
