import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useEventTracker } from "./event-tracker";

// The privacy-critical contract: postEvents must never receive anything
// beyond {type, t, x, y, dy} — no key identity, no clipboard, no media.
// The backend/ai schemas already enforce this on the wire (extra="forbid"
// — see ai/mirage_ai/schemas.py), but this is the regression guard on
// the *client* side: a future edit that adds e.g. `key: e.key` to a push
// call here should fail a test, not slip through to production.
const ALLOWED_KEYS = new Set(["type", "t", "x", "y", "dy"]);

vi.mock("@/lib/api-client", () => ({
  postEvents: vi.fn().mockResolvedValue({}),
}));

import { postEvents } from "@/lib/api-client";

describe("useEventTracker", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.mocked(postEvents).mockClear();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("does nothing when inactive or without a session id", () => {
    renderHook(() => useEventTracker(null, true));
    renderHook(() => useEventTracker("session-1", false));
    act(() => {
      window.dispatchEvent(new MouseEvent("click"));
      vi.advanceTimersByTime(2000);
    });
    expect(postEvents).not.toHaveBeenCalled();
  });

  it("batches real browser events and flushes only the allowed event shape", () => {
    renderHook(() => useEventTracker("session-1", true));

    act(() => {
      window.dispatchEvent(new MouseEvent("mousemove", { clientX: 12, clientY: 34 }));
      window.dispatchEvent(new MouseEvent("click"));
      window.dispatchEvent(new WheelEvent("wheel", { deltaY: 5 }));
      window.dispatchEvent(new KeyboardEvent("keydown", { key: "a" }));
      window.dispatchEvent(new KeyboardEvent("keyup", { key: "a" }));
      window.dispatchEvent(new Event("blur"));
      window.dispatchEvent(new Event("focus"));
      document.dispatchEvent(new Event("visibilitychange"));
    });

    act(() => {
      vi.advanceTimersByTime(1500); // FLUSH_INTERVAL_MS
    });

    expect(postEvents).toHaveBeenCalledTimes(1);
    const [sessionId, events] = vi.mocked(postEvents).mock.calls[0];
    expect(sessionId).toBe("session-1");
    expect(events.length).toBeGreaterThan(0);

    const types = events.map((e) => e.type);
    expect(types).toEqual(
      expect.arrayContaining([
        "mouse_move",
        "mouse_click",
        "scroll",
        "key_down",
        "key_up",
        "focus_lost",
        "focus_gained",
      ])
    );

    for (const event of events) {
      const keys = Object.keys(event);
      const disallowed = keys.filter((k) => !ALLOWED_KEYS.has(k));
      expect(disallowed).toEqual([]);
    }

    // The keyboard events specifically must never carry key identity —
    // the single most privacy-sensitive thing this hook must never leak.
    const keyEvents = events.filter((e) => e.type === "key_down" || e.type === "key_up");
    expect(keyEvents.length).toBeGreaterThan(0);
    for (const event of keyEvents) {
      expect(event).not.toHaveProperty("key");
      expect(event).not.toHaveProperty("code");
      expect(event).not.toHaveProperty("value");
    }
  });

  it("throttles rapid mouse_move events", () => {
    renderHook(() => useEventTracker("session-1", true));

    act(() => {
      for (let i = 0; i < 10; i++) {
        window.dispatchEvent(new MouseEvent("mousemove", { clientX: i, clientY: i }));
      }
    });
    act(() => {
      vi.advanceTimersByTime(1500);
    });

    const [, events] = vi.mocked(postEvents).mock.calls[0];
    const moveCount = events.filter((e) => e.type === "mouse_move").length;
    expect(moveCount).toBe(1); // throttled to one within MOUSE_MOVE_THROTTLE_MS
  });

  it("flushes remaining buffered events on unmount", () => {
    const { unmount } = renderHook(() => useEventTracker("session-1", true));
    act(() => {
      window.dispatchEvent(new MouseEvent("click"));
    });
    unmount();
    expect(postEvents).toHaveBeenCalledTimes(1);
  });
});
