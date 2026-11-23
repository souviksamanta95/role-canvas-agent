import { useId, useState, type FormEvent } from "react";
import type { Department, ProfileValues, User } from "../types";

interface Props {
  departments: Department[];
  user: User;
  submitLabel: string;
  onSubmit: (values: ProfileValues) => Promise<void>;
}

const REGION_SUGGESTIONS = ["EMEA", "NA", "APAC", "LATAM"];

/** Department first, then a role that belongs to that department. */
export function RoleDepartmentForm({ departments, user, submitLabel, onSubmit }: Props) {
  const [department, setDepartment] = useState(user.department ?? "");
  const [role, setRole] = useState(user.role ?? "");
  const [region, setRegion] = useState(user.region);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const ids = { dept: useId(), role: useId(), region: useId(), regions: useId() };

  const roles = departments.find((d) => d.slug === department)?.roles ?? [];
  const selectedRole = roles.find((r) => r.slug === role);
  // A role assigned by an administrator is not in the pickable list; show it so users understand.
  const assignedElsewhere = Boolean(user.role) && role === user.role && !selectedRole;

  function changeDepartment(next: string) {
    setDepartment(next);
    setRole(""); // a role only makes sense inside its own department
    setSaved(false);
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    setSaved(false);
    try {
      await onSubmit({ department, role, region: region.trim() });
      setSaved(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={submit} className="form">
      <div className="field">
        <label htmlFor={ids.dept}>Department</label>
        <select id={ids.dept} value={department} onChange={(e) => changeDepartment(e.target.value)}>
          <option value="">Select a department</option>
          {departments.map((d) => (
            <option key={d.slug} value={d.slug}>
              {d.name}
            </option>
          ))}
        </select>
      </div>

      <div className="field">
        <label htmlFor={ids.role}>Role</label>
        <select
          id={ids.role}
          value={role}
          disabled={!department}
          onChange={(e) => {
            setRole(e.target.value);
            setSaved(false);
          }}
        >
          <option value="">{department ? "Select a role" : "Choose a department first"}</option>
          {roles.map((r) => (
            <option key={r.slug} value={r.slug}>
              {r.name}
            </option>
          ))}
        </select>
        {selectedRole?.description && <p className="hint">{selectedRole.description}</p>}
        {assignedElsewhere && (
          <p className="hint">
            Your current role was assigned by an administrator. Pick another role to replace it.
          </p>
        )}
        {department && roles.length === 0 && <p className="hint">No roles are available to pick in this department.</p>}
      </div>

      <div className="field">
        <label htmlFor={ids.region}>
          Region <span className="optional">(optional)</span>
        </label>
        <input
          id={ids.region}
          value={region}
          maxLength={50}
          list={ids.regions}
          onChange={(e) => {
            setRegion(e.target.value);
            setSaved(false);
          }}
          placeholder="e.g. EMEA"
        />
        <datalist id={ids.regions}>
          {REGION_SUGGESTIONS.map((r) => (
            <option key={r} value={r} />
          ))}
        </datalist>
        <p className="hint">Some roles only see data for your region.</p>
      </div>

      {error && (
        <p className="alert error" role="alert">
          {error}
        </p>
      )}
      {saved && (
        <p className="alert ok" role="status">
          Saved. Your access has been updated.
        </p>
      )}
      <button className="btn primary" type="submit" disabled={!department || !role || saving}>
        {saving ? "Saving..." : submitLabel}
      </button>
    </form>
  );
}
