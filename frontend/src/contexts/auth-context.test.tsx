import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { AuthProvider, useAuth } from "./auth-context";

vi.mock("@/lib/api-client", () => ({
  ApiError: class ApiError extends Error {
    status: number;
    constructor(message: string, status: number) {
      super(message);
      this.status = status;
    }
  },
  getMe: vi.fn(),
  login: vi.fn(),
  signup: vi.fn(),
  setAuthToken: vi.fn(),
}));

import { getMe, login as apiLogin, setAuthToken, signup as apiSignup } from "@/lib/api-client";

const RAW_USER = { userId: "u1", orgId: "org1", email: "ada@acme.com", role: "owner" };

function wrapper({ children }: { children: React.ReactNode }) {
  return <AuthProvider>{children}</AuthProvider>;
}

describe("AuthProvider", () => {
  beforeEach(() => {
    vi.mocked(getMe).mockReset();
    vi.mocked(apiLogin).mockReset();
    vi.mocked(apiSignup).mockReset();
    vi.mocked(setAuthToken).mockReset();
  });

  it("starts loading, then authenticates if a stored token is still valid", async () => {
    vi.mocked(getMe).mockResolvedValue(RAW_USER);
    const { result } = renderHook(() => useAuth(), { wrapper });

    expect(result.current.isLoading).toBe(true);
    expect(result.current.isAuthenticated).toBe(false);

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.user?.email).toBe("ada@acme.com");
  });

  it("clears the stored token and stays logged out if it's no longer valid", async () => {
    vi.mocked(getMe).mockRejectedValue(new Error("401"));
    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
    expect(setAuthToken).toHaveBeenCalledWith(null);
  });

  it("login() stores the returned token and authenticates the user", async () => {
    vi.mocked(getMe).mockRejectedValue(new Error("no token yet"));
    vi.mocked(apiLogin).mockResolvedValue({ accessToken: "tok-123", tokenType: "bearer", user: RAW_USER });

    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    await act(async () => {
      await result.current.login("ada@acme.com", "password123");
    });

    expect(apiLogin).toHaveBeenCalledWith({ email: "ada@acme.com", password: "password123" });
    expect(setAuthToken).toHaveBeenCalledWith("tok-123");
    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.user?.email).toBe("ada@acme.com");
  });

  it("signup() stores the returned token, authenticates, and records the org name", async () => {
    vi.mocked(getMe).mockRejectedValue(new Error("no token yet"));
    vi.mocked(apiSignup).mockResolvedValue({ accessToken: "tok-456", tokenType: "bearer", user: RAW_USER });

    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    await act(async () => {
      await result.current.signup("Acme Inc", "ada@acme.com", "password123");
    });

    expect(apiSignup).toHaveBeenCalledWith({
      orgName: "Acme Inc",
      email: "ada@acme.com",
      password: "password123",
    });
    expect(setAuthToken).toHaveBeenCalledWith("tok-456");
    expect(result.current.user?.organization).toBe("Acme Inc");
  });

  it("logout() clears the token and the user", async () => {
    vi.mocked(getMe).mockResolvedValue(RAW_USER);
    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.isAuthenticated).toBe(true);

    act(() => {
      result.current.logout();
    });

    expect(setAuthToken).toHaveBeenCalledWith(null);
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
  });

  it("useAuth throws outside an AuthProvider", () => {
    expect(() => renderHook(() => useAuth())).toThrow("useAuth must be used within AuthProvider");
  });
});
