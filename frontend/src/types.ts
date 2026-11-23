export interface User {
  id: number;
  email: string;
  full_name: string;
  picture_url: string;
  department: string | null;
  role: string | null;
  region: string;
  needs_onboarding: boolean;
}

export interface RoleOption {
  slug: string;
  name: string;
  description: string;
}

export interface Department {
  slug: string;
  name: string;
  description: string;
  roles: RoleOption[];
}

export interface Tokens {
  access: string;
  refresh: string;
}

export interface AuthResponse extends Tokens {
  user: User;
}

export interface RowFilter {
  column: string;
  op: string;
  value: unknown;
}

export interface Grant {
  role: string | null;
  columns: string[];
  row_filter: RowFilter[];
  aggregate_only: boolean;
  min_group_size: number;
}

export interface DatasetAccess {
  slug: string;
  name: string;
  description: string;
  sensitivity: string;
  grants: Grant[];
}

export interface DeniedDataset {
  slug: string;
  name: string;
  reason: string;
}

export interface AccessPolicy {
  datasets: DatasetAccess[];
  denied: DeniedDataset[];
}

export interface ProfileValues {
  department: string;
  role: string;
  region: string;
}
