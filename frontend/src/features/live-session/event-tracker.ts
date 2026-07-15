import * as React from "react";
import { postEvents } from "@/lib/api-client";
import type { RawEventOut } from "@/types/api";

const MOUSE_MOVE_THROTTLE_MS = 120;
const FLUSH_INTERVAL_MS = 1500;

// Attaches real browser listeners and batches them to the backend. Never
// reads key identity, clipboard, or any field beyond {type, t, x, y, dy} —
// matches ai/'s RawEvent schema exactly (see ai/mirage_ai/schemas.py),
// which physically cannot accept anything more.
export function useEventTracker(sessionId: string | null, active: boolean): void {
  const bufferRef = React.useRef<RawEventOut[]>([]);
  const lastMouseMoveAtRef = React.useRef(0);

  React.useEffect(() => {
    if (!active || !sessionId) return;

    const push = (event: RawEventOut) => bufferRef.current.push(event);

    const onMouseMove = (e: MouseEvent) => {
      const now = Date.now();
      if (now - lastMouseMoveAtRef.current < MOUSE_MOVE_THROTTLE_MS) return;
      lastMouseMoveAtRef.current = now;
      push({ type: "mouse_move", t: now, x: e.clientX, y: e.clientY });
    };
    const onClick = () => push({ type: "mouse_click", t: Date.now() });
    const onWheel = (e: WheelEvent) => push({ type: "scroll", t: Date.now(), dy: e.deltaY });
    const onKeyDown = () => push({ type: "key_down", t: Date.now() });
    const onKeyUp = () => push({ type: "key_up", t: Date.now() });
    const onBlur = () => push({ type: "focus_lost", t: Date.now() });
    const onFocus = () => push({ type: "focus_gained", t: Date.now() });
    const onVisibility = () =>
      push({ type: document.hidden ? "visibility_hidden" : "visibility_visible", t: Date.now() });

    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("click", onClick);
    window.addEventListener("wheel", onWheel, { passive: true });
    window.addEventListener("keydown", onKeyDown);
    window.addEventListener("keyup", onKeyUp);
    window.addEventListener("blur", onBlur);
    window.addEventListener("focus", onFocus);
    document.addEventListener("visibilitychange", onVisibility);

    const flush = () => {
      if (bufferRef.current.length === 0) return;
      const batch = bufferRef.current;
      bufferRef.current = [];
      postEvents(sessionId, batch).catch(() => {
        // Best-effort: a dropped batch just means fewer signals feed the
        // next tick — never worth failing the interview over.
      });
    };
    const flushTimer = window.setInterval(flush, FLUSH_INTERVAL_MS);

    return () => {
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("click", onClick);
      window.removeEventListener("wheel", onWheel);
      window.removeEventListener("keydown", onKeyDown);
      window.removeEventListener("keyup", onKeyUp);
      window.removeEventListener("blur", onBlur);
      window.removeEventListener("focus", onFocus);
      document.removeEventListener("visibilitychange", onVisibility);
      window.clearInterval(flushTimer);
      flush();
    };
  }, [sessionId, active]);
}
