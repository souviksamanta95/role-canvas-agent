import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";
import { AuthProvider } from "./auth";
import { departments, newUser, onboardedUser } from "./test/fixtures";
import type { User } from "./types";

vi.mock("./api", () => {
  let session = false;
  return {
    __setSession: (value: boolean) => (session = value),
    setTokens: vi.fn(),
    hasStoredSession: () => session,
    refreshSession: vi.fn().mockResolvedValue(true),
    api: {
      me: vi.fn(),
      departments: vi.fn(),
      access: vi.fn(),
      logout: vi.fn().mockResolvedValue(undefined),
      loginWithGoogle: vi.fn(),
      updateProfile: vi.fn(),
    },
  };
});
vi.mock("./config", () => ({ getGoogleClientId: () => "" , BACKEND_URL: "http://test"}));

import * as apiModule from "./api";

const mocked = apiModule as unknown as {
  __setSession: (v: boolean) => void;
  api: Record<string, ReturnType<typeof vi.fn>>;
};

function renderAt(path: string, signedInAs: User | null) {
  mocked.__setSession(signedInAs !== null);
  if (signedInAs) mocked.api.me.mockResolvedValue(signedInAs);
  mocked.api.departments.mockResolvedValue(departments);
  mocked.api.access.mockResolvedValue({
    datasets: [
      {
        slug: "finance-revenue-summary",
        name: "Revenue by month",
        description: "",
        sensitivity: "Internal",
        grants: [{ role: "finance-analyst", columns: ["a", "b"], row_filter: [], aggregate_only: true, min_group_size: 5 }],
      },
    ],
    denied: [{ slug: "hr-payroll", name: "Employee payroll", reason: "no_grant" }],
  });
  return render(
    <MemoryRouter initialEntries={[path]}>
      <AuthProvider>
        <App />
      </AuthProvider>
    </MemoryRouter>,
  );
}

describe("routing", () => {
  beforeEach(() => vi.clearAllMocks());

  it("sends anonymous visitors to the login page", async () => {
    renderAt("/dashboard", null);
    expect(await screen.findByRole("heading", { name: "RoleCanvas" })).toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent("Google sign-in is not configured");
  });

  it("forces first-time users through onboarding", async () => {
    renderAt("/dashboard", newUser);
    expect(await screen.findByText(/Tell us where you work/)).toBeInTheDocument();
    expect(screen.getByLabelText("Role")).toBeDisabled();
  });

  it("shows the dashboard with the user's data access", async () => {
    renderAt("/dashboard", onboardedUser);
    expect(await screen.findByRole("heading", { name: "Dashboard" })).toBeInTheDocument();
    expect(await screen.findByText("Revenue by month")).toBeInTheDocument();
    expect(screen.getByText(/Aggregates only \(groups of 5\+\)/)).toBeInTheDocument();
    expect(screen.getByText(/1 datasets are not available to you/)).toBeInTheDocument();
    expect(screen.getByLabelText("Chart prompt (planned)")).toBeDisabled();
  });

  it("lets a signed-in user change department and role on the profile page", async () => {
    renderAt("/profile", onboardedUser);
    expect(await screen.findByRole("heading", { name: "Profile" })).toBeInTheDocument();
    expect(await screen.findByLabelText("Department")).toHaveValue("finance");
    expect(screen.getByLabelText("Role")).toHaveValue("finance-analyst");
  });

  it("sends onboarded users away from the onboarding page", async () => {
    renderAt("/onboarding", onboardedUser);
    expect(await screen.findByRole("heading", { name: "Dashboard" })).toBeInTheDocument();
  });
});
