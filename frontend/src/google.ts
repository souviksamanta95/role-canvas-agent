interface CredentialResponse {
  credential: string;
}

interface GoogleIdentity {
  accounts: {
    id: {
      initialize: (config: { client_id: string; callback: (r: CredentialResponse) => void }) => void;
      renderButton: (element: HTMLElement, options: Record<string, string | number>) => void;
    };
  };
}

declare global {
  interface Window {
    google?: GoogleIdentity;
  }
}

const SRC = "https://accounts.google.com/gsi/client";
let loading: Promise<GoogleIdentity> | null = null;

/** Load Google's sign-in script once and resolve with its API. */
export function loadGoogle(): Promise<GoogleIdentity> {
  if (window.google) return Promise.resolve(window.google);
  loading ??= new Promise<GoogleIdentity>((resolve, reject) => {
    const script = document.createElement("script");
    script.src = SRC;
    script.async = true;
    script.onload = () => (window.google ? resolve(window.google) : reject(new Error("Google script missing")));
    script.onerror = () => {
      loading = null;
      reject(new Error("Could not load Google sign-in. Check your connection or ad blocker."));
    };
    document.head.appendChild(script);
  });
  return loading;
}
