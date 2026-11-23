import { useAuth } from "../auth";
import { RoleDepartmentForm } from "../components/RoleDepartmentForm";

export function ProfilePage() {
  const { user, departments, updateProfile } = useAuth();
  if (!user) return null;

  return (
    <div className="stack">
      <h1>Profile</h1>
      <section className="card">
        <h2>Account</h2>
        <dl className="facts">
          <dt>Name</dt>
          <dd>{user.full_name || "Not provided"}</dd>
          <dt>Email</dt>
          <dd>{user.email}</dd>
        </dl>
        <p className="hint">Your name and email come from your Google account.</p>
      </section>
      <section className="card">
        <h2>Department and role</h2>
        <p className="lead">
          You can change these at any time. Your dashboard access updates immediately. Some sensitive roles are assigned by an
          administrator and are not listed here.
        </p>
        {/* key remounts the form when the saved values change so it shows the new state */}
        <RoleDepartmentForm
          key={`${user.department}/${user.role}/${user.region}`}
          departments={departments}
          user={user}
          submitLabel="Save changes"
          onSubmit={async (values) => {
            await updateProfile(values);
          }}
        />
      </section>
    </div>
  );
}
