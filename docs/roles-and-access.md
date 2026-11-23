# Roles, departments and data access

Status: backend and the frontend sign-in, onboarding, dashboard and profile screens are implemented; agent enforcement is planned. The demo datasets are
**synthetic placeholders**; real public datasets will be listed in `data/README.md` as chosen.

## Principles

- **Deny by default.** Nothing is visible unless a grant allows it.
- **The server decides, never the LLM.** Access is resolved from the database on every request.
- **Frontend talks only to Django.** Django resolves the user's access and (in Phase 1) passes it to
  the agent over the internal network. The browser never reaches the agent or Postgres directly.
- **Two schemas.** `public` holds auth and RBAC (owned by Django). `datasets` holds the data the
  agent may query. The agent's read-only Postgres role has `SELECT` on `datasets` only and no
  access to `public`, so it can never read users or grants.

## Model

| Concept | Meaning |
|---|---|
| Department | Finance, HR, Marketing... Owns datasets; users belong to one. |
| Role | Belongs to one department. Has a sensitivity **ceiling** and an `is_self_selectable` flag. |
| Sensitivity | `public` < `internal` < `confidential` < `restricted`, set per dataset and per column. |
| Dataset | Catalog entry: owner department, sensitivity, storage (`postgres` table in `datasets`, or `parquet` path), row limit. |
| Column | Name, type, sensitivity, `is_pii`. PII must be Confidential or higher. |
| Grant | Role to dataset: allowed **columns**, optional **row filter**, optional **aggregate-only** with a **minimum group size**. |
| RoleAssignment | Extra role given to a user by an admin, optionally with an expiry. |

### Rules

1. Public datasets are visible to every signed-in user (public, non-PII columns only).
2. Any other dataset needs a grant on one of the user's active roles.
3. A grant is ignored when the dataset is above the role's ceiling (`above_role_sensitivity_ceiling`).
4. Only columns listed in the grant **and** at or below the ceiling are visible.
5. **Grants are never merged.** A query must fit entirely inside one grant, so two narrow grants
   cannot be combined into a wider one.
6. A row filter is a list of conditions ANDed together: `{"column", "op", "value"}`. Operators:
   `eq`, `neq`, `in`, `lt`, `lte`, `gt`, `gte`. `"$user.region"` is replaced by the user's region;
   if the user has none, the grant is skipped (`missing_user_region`). It fails closed.
7. Aggregate-only grants allow only aggregated results, and only when every group has at least
   `min_group_size` rows. An unknown group size is treated as too small.
8. Roles with a **Restricted** ceiling can never be self-selectable.

`catalog/policy.py` has `resolve_policy(user)` (what the user may access) and `decide(...)`
(whether a specific query is allowed, with a reason code). The agent will mirror `decide`.

## Sign-in and tokens

- Normal users sign in **only with Google**. The frontend sends the Google ID token to
  `POST /api/auth/google/`; the backend verifies it (audience, signature, verified email,
  optional domain allow-list) and returns our own JWT pair. Normal users have no password.
- Admins sign in to `/admin/` with an email and password created by `make superuser`.
- Access tokens last 15 minutes and refresh tokens 7 days. Refresh tokens rotate and are
  blacklisted after use. Tokens are signed with `JWT_SIGNING_KEY` (separate from `DJANGO_SECRET_KEY`).
- Each token carries `pv`, the user's **policy version**. It increases when the user's department,
  role, region or active flag changes, and old access tokens are then rejected (401 `token_stale`).
  The client refreshes (or uses the new pair returned by `PATCH /api/me/`).

## First-time and later role changes

A new user has no department or role (`needs_onboarding: true`) and sees public data only. They pick
a **department first, then a role inside it**, from `GET /api/departments/`, and can change both
any time with `PATCH /api/me/`. Only roles with `is_self_selectable` appear. Sensitive roles
(Auditor, Payroll Specialist, Compliance Officer, Platform Admin) are assigned by an admin.

Because users choose their own role, this is a **demo of access control, not a production
authorization system** (see the README's Limitations). Restricting sign-in with
`ALLOWED_EMAIL_DOMAINS` and keeping sensitive roles non-self-selectable limits the exposure.

## API

| Method and path | Auth | Purpose |
|---|---|---|
| `POST /api/auth/google/` | none | `{id_token}` returns `{access, refresh, user}`. 503 if Google is not configured. |
| `POST /api/auth/refresh/` | none | `{refresh}` returns a new `{access, refresh}`; the old refresh token is revoked. |
| `POST /api/auth/logout/` | none | `{refresh}` revokes it. 204. |
| `GET /api/me/` | JWT | Profile, department, role, `needs_onboarding`. |
| `PATCH /api/me/` | JWT | `{department?, role?, region?}`. Returns a fresh token pair. |
| `GET /api/departments/` | JWT | Departments with their self-selectable roles (for the dropdowns). |
| `GET /api/me/access/` | JWT | The user's resolved access: allowed datasets, grants, denied datasets with reasons. |
| `GET /health/` | none | Liveness. |

Auth endpoints are rate limited (20 per minute).

## Admin workflow (`/admin/`)

1. **Departments and Roles**: create a role, set its department, sensitivity ceiling and whether
   users may pick it. The role page shows its data grants inline. "Duplicate role" copies a role
   and its grants as non-self-selectable so it can be reviewed first.
2. **Datasets**: register a dataset and its columns (type, sensitivity, PII flag).
3. **Grants**: on a role page, add a dataset, save, then choose the allowed columns, row filter
   and aggregate-only settings. Column choices are limited to the chosen dataset.
4. **Users**: set department and role, or add **role assignments** with an optional expiry
   (for example a time-boxed Auditor). Saving changes bumps the policy version.
5. **Access audit log**: read-only record of allow and deny decisions.

## Seeded departments and roles

`make seed` loads these (grants exist only where a dataset applies; "none yet" roles can still be
selected and see public data until datasets are added).

| Department | Roles (admin-only in bold) |
|---|---|
| Finance | Finance Analyst, FP&A Analyst, Controller, AP/AR Clerk, **Auditor** |
| Marketing | Marketing Analyst, Performance Marketer, Marketing Manager |
| Operations | Operations Analyst, Logistics Coordinator, Operations Manager, Procurement |
| Executive | Executive, Board Viewer |
| Sales | Sales Representative (own region), Sales Manager, RevOps Analyst |
| HR | HR Business Partner, HR Manager, Recruiter, **Payroll Specialist** |
| Product | Product Manager, Product Analyst, UX Researcher |
| Customer Support | Support Agent, Support Manager |
| Legal & Compliance | **Compliance Officer**, Legal Counsel |
| Engineering & Data | Engineer, Data Analyst, Data Steward |
| General | Guest, **Platform Admin** (manages roles, no data access) |

## Access cases covered by tests

Finance analyst refused payroll; marketer gets sales only as aggregates with a minimum group size
and never customer ids; sales rep limited to their region (and nothing without a region);
executive never sees payroll or restricted columns; grants above a role's ceiling ignored;
reclassifying a dataset upward removes access; grants not merged across roles; time-boxed
assignment expires; inactive role or user gets nothing; role change invalidates old tokens;
users cannot self-assign admin-only roles; dataset text cannot change access.

## Setting up Google sign-in

1. In Google Cloud Console, create an OAuth client ID of type **Web application**.
2. Add `http://localhost:3000` under Authorized JavaScript origins.
3. Put the client ID in `GOOGLE_OAUTH_CLIENT_ID` in `.env`. The frontend reads the same variable (recreate the containers with `make up`, or restart `make dev-frontend`).
4. Optionally set `ALLOWED_EMAIL_DOMAINS`.

Until it is set, `make dev-token EMAIL=you@example.com` issues a token for local testing. It
refuses to run unless `DJANGO_DEBUG=True`.
