import { apiFetch, tokenStorage } from "@/api/client";
import type { User } from "@/types";

interface LoginResponse {
  access_token: string;
  user: User;
}

export async function loginGuest(): Promise<LoginResponse> {
  const res = await apiFetch<LoginResponse>("/api/auth/login", {
    method: "POST",
    body: { mode: "guest" },
  });
  tokenStorage.set(res.access_token);
  return res;
}

export async function loginMicrosoft(email: string, name: string): Promise<LoginResponse> {
  const res = await apiFetch<LoginResponse>("/api/auth/login", {
    method: "POST",
    body: { mode: "microsoft", email, name },
  });
  tokenStorage.set(res.access_token);
  return res;
}

export async function loginPassword(email: string, password: string): Promise<LoginResponse> {
  const res = await apiFetch<LoginResponse>("/api/auth/login", {
    method: "POST",
    body: { mode: "password", email, password },
  });
  tokenStorage.set(res.access_token);
  return res;
}

export async function signupPassword(email: string, password: string, name: string): Promise<LoginResponse> {
  const res = await apiFetch<LoginResponse>("/api/auth/login", {
    method: "POST",
    body: { mode: "signup", email, password, name },
  });
  tokenStorage.set(res.access_token);
  return res;
}

export async function logout(): Promise<void> {
  try {
    await apiFetch("/api/auth/logout", { method: "POST" });
  } finally {
    tokenStorage.clear();
  }
}

export async function fetchMe(): Promise<User> {
  return apiFetch<User>("/api/auth/me");
}
