import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../auth";

export function Layout() {
  const { user, departments, logout } = useAuth();
  const department = departments.find((d) => d.slug === user?.department);
  const role = department?.roles.find((r) => r.slug === user?.role);
  const initial = (user?.full_name || user?.email || "?").charAt(0).toUpperCase();

  return (
    <div className="shell">
      <header className="topbar">
        <span className="brand">RoleCanvas</span>
        <nav aria-label="Main">
          <NavLink to="/dashboard">Dashboard</NavLink>
          <NavLink to="/profile">Profile</NavLink>
        </nav>
        <div className="userchip">
          {user?.picture_url ? (
            <img src={user.picture_url} alt="" referrerPolicy="no-referrer" className="avatar" />
          ) : (
            <span className="avatar fallback" aria-hidden="true">
              {initial}
            </span>
          )}
          <div className="who">
            <strong>{user?.full_name || user?.email}</strong>
            <span>{[department?.name, role?.name ?? user?.role].filter(Boolean).join(" / ")}</span>
          </div>
          <button className="btn" onClick={() => void logout()}>
            Sign out
          </button>
        </div>
      </header>
      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}
