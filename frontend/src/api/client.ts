const API_BASE = import.meta.env.VITE_API_URL || "";
const TOKEN_KEY = "nutriai_token";

export const tokenStorage = {
  get: () => localStorage.getItem(TOKEN_KEY),
  set: (t: string) => localStorage.setItem(TOKEN_KEY, t),
  clear: () => localStorage.removeItem(TOKEN_KEY),
};

export class ApiError extends Error {
  status: number;
  body: unknown;
  constructor(status: number, message: string, body: unknown) {
    super(message);
    this.status = status;
    this.body = body;
  }
}

type FetchOptions = Omit<RequestInit, "body"> & { body?: unknown; raw?: boolean };

export async function apiFetch<T>(path: string, opts: FetchOptions = {}): Promise<T> {
  const headers = new Headers(opts.headers);
  if (!(opts.body instanceof FormData) && opts.body !== undefined) {
    headers.set("Content-Type", "application/json");
  }
  const token = tokenStorage.get();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const init: RequestInit = {
    ...opts,
    headers,
    credentials: "include",
    body:
      opts.body === undefined
        ? undefined
        : opts.body instanceof FormData
          ? (opts.body as BodyInit)
          : JSON.stringify(opts.body),
  };

  const res = await fetch(`${API_BASE}${path}`, init);
  if (res.status === 204) return undefined as T;

  const ct = res.headers.get("content-type") ?? "";
  const data = ct.includes("application/json") ? await res.json() : await res.text();

  if (!res.ok) {
    const message =
      typeof data === "object" && data && "detail" in (data as object)
        ? String((data as { detail: unknown }).detail)
        : res.statusText;
    throw new ApiError(res.status, message, data);
  }
  return data as T;
}

export function imageUrl(url: string | null | undefined): string | undefined {
  if (!url) return undefined;
  if (url.startsWith("http")) return url;
  return `${API_BASE}${url}`;
}
