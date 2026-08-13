import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { CreateSessionForm } from "./create-session-form";

// The compliance-critical behavior: submission must be impossible without
// checking the tracking-disclosure box, and once submitted, the backend
// must actually be told about the disclosure via /consent before the
// session itself is created (see the roadmap's Phase 7 consent gate).
vi.mock("@/lib/api-client", () => ({
  createSession: vi.fn(),
  acceptConsent: vi.fn(),
}));

import { acceptConsent, createSession } from "@/lib/api-client";

async function fillRequiredFields(user: ReturnType<typeof userEvent.setup>) {
  // Sequential, not Promise.all — userEvent's `type()` drives an internal
  // per-session state machine that two concurrent calls on the same
  // `user` corrupt (fields silently end up empty), which is exactly what
  // caused this helper's first version to fail every test using it.
  await user.type(screen.getByLabelText(/candidate name/i), "Ada Lovelace");
  await user.type(screen.getByLabelText(/observer name/i), "Bob");
}

describe("CreateSessionForm", () => {
  beforeEach(() => {
    vi.mocked(createSession).mockReset();
    vi.mocked(acceptConsent).mockReset();
    vi.mocked(acceptConsent).mockResolvedValue({
      document: "session_tracking_notice",
      version: "2026-08-13",
      acceptedAt: "2026-01-01T00:00:00Z",
    });
    vi.mocked(createSession).mockResolvedValue({
      sessionId: "s1",
      candidateName: "Ada Lovelace",
      interviewType: "Technical Interview",
      status: "active",
    });
  });

  function renderForm() {
    const onCreate = vi.fn();
    const onCancel = vi.fn();
    render(
      <MemoryRouter>
        <CreateSessionForm onCreate={onCreate} onCancel={onCancel} />
      </MemoryRouter>
    );
    return { onCreate, onCancel };
  }

  it("blocks submission until the tracking-disclosure checkbox is checked", async () => {
    const user = userEvent.setup();
    const { onCreate } = renderForm();
    await fillRequiredFields(user);

    await user.click(screen.getByRole("button", { name: /create session/i }));

    // The disclosure text appears twice (the checkbox label itself, plus
    // the validation error once submission is blocked) — scope to the
    // error paragraph specifically rather than matching either.
    const error = await screen.findByText(/confirm the candidate has been informed before starting/i);
    expect(error.tagName).toBe("P");
    expect(createSession).not.toHaveBeenCalled();
    expect(onCreate).not.toHaveBeenCalled();
  });

  it("submits and records session_tracking_notice consent once the box is checked", async () => {
    const user = userEvent.setup();
    const { onCreate } = renderForm();
    await fillRequiredFields(user);
    await user.click(screen.getByRole("checkbox"));
    await user.click(screen.getByRole("button", { name: /create session/i }));

    await waitFor(() => expect(createSession).toHaveBeenCalledTimes(1));
    expect(acceptConsent).toHaveBeenCalledWith({
      document: "session_tracking_notice",
      version: "2026-08-13",
    });
    expect(onCreate).toHaveBeenCalledWith(expect.objectContaining({ sessionId: "s1" }));
  });

  it("still creates the session even if the best-effort consent call fails", async () => {
    vi.mocked(acceptConsent).mockRejectedValue(new Error("network error"));
    const user = userEvent.setup();
    const { onCreate } = renderForm();
    await fillRequiredFields(user);
    await user.click(screen.getByRole("checkbox"));
    await user.click(screen.getByRole("button", { name: /create session/i }));

    await waitFor(() => expect(onCreate).toHaveBeenCalled());
  });

  it("shows an error and does not call onCreate when session creation fails", async () => {
    vi.mocked(createSession).mockRejectedValue(new Error("boom"));
    const user = userEvent.setup();
    const { onCreate } = renderForm();
    await fillRequiredFields(user);
    await user.click(screen.getByRole("checkbox"));
    await user.click(screen.getByRole("button", { name: /create session/i }));

    expect(await screen.findByText(/couldn't reach the behavioral intelligence service/i)).toBeInTheDocument();
    expect(onCreate).not.toHaveBeenCalled();
  });
});
