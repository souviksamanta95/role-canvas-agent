import type { Department, User } from "../types";

export const departments: Department[] = [
  {
    slug: "finance",
    name: "Finance",
    description: "",
    roles: [
      { slug: "finance-analyst", name: "Finance Analyst", description: "Revenue and budget aggregates." },
      { slug: "controller", name: "Controller", description: "Full ledger." },
    ],
  },
  {
    slug: "marketing",
    name: "Marketing",
    description: "",
    roles: [{ slug: "marketing-analyst", name: "Marketing Analyst", description: "Campaign results." }],
  },
];

export const newUser: User = {
  id: 1,
  email: "jane@example.com",
  full_name: "Jane Doe",
  picture_url: "",
  department: null,
  role: null,
  region: "",
  needs_onboarding: true,
};

export const onboardedUser: User = {
  ...newUser,
  department: "finance",
  role: "finance-analyst",
  needs_onboarding: false,
};
