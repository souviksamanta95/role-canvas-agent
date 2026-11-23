import { useEffect, useState } from "react";
import { api } from "../api";
import { useAuth } from "../auth";
import type { AccessPolicy, DatasetAccess } from "../types";

const REASONS: Record<string, string> = {
  no_grant: "Not granted to your role",
  above_role_sensitivity_ceiling: "More sensitive than your role allows",
  missing_user_region: "Needs a region on your profile",
};

function describe(dataset: DatasetAccess): string[] {
  const notes: string[] = [];
  for (const grant of dataset.grants) {
    if (grant.aggregate_only) notes.push(`Aggregates only (groups of ${grant.min_group_size}+)`);
    for (const f of grant.row_filter) notes.push(`Limited to ${f.column} ${f.op === "eq" ? "=" : f.op} ${String(f.value)}`);
  }
  return [...new Set(notes)];
}

export function DashboardPage() {
  const { user, departments } = useAuth();
  const [policy, setPolicy] = useState<AccessPolicy | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    api
      .access()
      .then((p) => !cancelled && setPolicy(p))
      .catch((err: unknown) => !cancelled && setError(err instanceof Error ? err.message : "Could not load your access."));
    return () => {
      cancelled = true;
    };
  }, [user?.role, user?.department, user?.region]);

  const department = departments.find((d) => d.slug === user?.department);
  const role = department?.roles.find((r) => r.slug === user?.role);

  return (
    <div className="stack">
      <div>
        <h1>Dashboard</h1>
        <p className="lead">
          Signed in as <strong>{role?.name ?? user?.role}</strong>
          {department ? ` in ${department.name}` : ""}.
        </p>
      </div>

      <section className="card">
        <h2>Canvas</h2>
        <div className="canvas" aria-label="Chart canvas placeholder">
          <p>Charts will appear here.</p>
          <span className="planned">Planned</span>
        </div>
        <div className="prompt">
          <input disabled placeholder="Describe what you want to see (planned)" aria-label="Chart prompt (planned)" />
          <button className="btn primary" disabled>
            Build charts
          </button>
        </div>
      </section>

      <section className="card">
        <h2>Your data access</h2>
        {error && (
          <p className="alert error" role="alert">
            {error}
          </p>
        )}
        {!policy && !error && <p className="hint">Loading...</p>}
        {policy && policy.datasets.length === 0 && <p className="hint">No datasets are available to your role yet.</p>}
        {policy && policy.datasets.length > 0 && (
          <ul className="datasets">
            {policy.datasets.map((d) => (
              <li key={d.slug}>
                <div className="row">
                  <strong>{d.name}</strong>
                  <span className={`tag ${d.sensitivity.toLowerCase()}`}>{d.sensitivity}</span>
                </div>
                <p className="hint">
                  {Math.max(...d.grants.map((g) => g.columns.length))} columns
                  {describe(d).length > 0 ? ` · ${describe(d).join(" · ")}` : ""}
                </p>
              </li>
            ))}
          </ul>
        )}
        {policy && policy.denied.length > 0 && (
          <details>
            <summary>{policy.denied.length} datasets are not available to you</summary>
            <ul className="datasets muted">
              {policy.denied.map((d) => (
                <li key={d.slug}>
                  {d.name} <span className="hint">· {REASONS[d.reason] ?? d.reason}</span>
                </li>
              ))}
            </ul>
          </details>
        )}
      </section>
    </div>
  );
}
