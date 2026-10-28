import { useEffect, useRef, useState } from "react";
import { SubmissionFailure } from "./api.js";
import type {
  Principal,
  SavedPlan,
  SessionRecord,
  SessionSubmission,
  TrainingApi,
} from "./api.js";
import { canonical, StreamError } from "./sse.js";

type Selection = {
  status: "" | SessionSubmission["status"];
  effort: string;
  rating: string;
};
const empty: Selection = { status: "", effort: "", rating: "" };
type Pending = { day: number; body: SessionSubmission };

export function CompletionPanel({
  api,
  principal,
  plan,
}: {
  api: TrainingApi;
  principal: Principal;
  plan: SavedPlan;
}) {
  const [rows, setRows] = useState<SessionRecord[]>([]);
  const [choices, setChoices] = useState<Record<number, Selection>>({});
  const [loaded, setLoaded] = useState(false);
  const [busy, setBusy] = useState(false);
  const [blocked, setBlocked] = useState(false);
  const [pending, setPending] = useState<Pending | null>(null);
  const [message, setMessage] = useState("Loading submitted session records…");
  const active = useRef<AbortController | null>(null);
  const alive = useRef(true);

  async function read() {
    if (active.current) return;
    const controller = new AbortController();
    active.current = controller;
    setBusy(true);
    try {
      const records = await api.completions(principal, plan, controller.signal);
      if (!alive.current || controller.signal.aborted) return;
      setRows(records);
      setLoaded(true);
      setMessage(
        "Only submitted records are shown. Approval does not record completion.",
      );
    } catch {
      if (alive.current && !controller.signal.aborted) {
        setLoaded(false);
        setMessage(
          "Session records could not be read. Reload before submitting.",
        );
      }
    } finally {
      if (alive.current && active.current === controller) {
        active.current = null;
        setBusy(false);
      }
    }
  }
  useEffect(() => {
    alive.current = true;
    void read();
    return () => {
      alive.current = false;
      active.current?.abort();
      active.current = null;
    };
    // Parent keys this panel by principal and immutable approved plan identity.
  }, [api, principal, plan]);

  function change(day: number, field: keyof Selection, value: string) {
    setChoices((prior) => {
      const next = { ...empty, ...prior[day], [field]: value };
      if (next.status === "skipped") {
        next.effort = "";
        next.rating = "";
      }
      return { ...prior, [day]: next };
    });
  }

  async function submit(day: number) {
    if (active.current || !loaded || blocked) return;
    const selected = choices[day] ?? empty;
    if (
      !pending &&
      (!selected.status || rows.some((row) => row.day_index === day))
    )
      return;
    const attempt = pending ?? {
      day,
      body: {
        expected_revision: 0,
        plan_revision: plan.approval.candidate.revision,
        plan_content_hash: plan.approval.candidate.content_hash,
        idempotency_key: crypto.randomUUID(),
        status: selected.status as SessionSubmission["status"],
        effort: (selected.effort || null) as SessionSubmission["effort"],
        rating: selected.rating ? Number(selected.rating) : null,
      },
    };
    const controller = new AbortController();
    active.current = controller;
    setPending(attempt);
    setBusy(true);
    setMessage("Submitting your session record…");
    try {
      const accepted = await api.submitSession(
        principal,
        plan,
        attempt.day,
        attempt.body,
        controller.signal,
      );
      if (!alive.current || controller.signal.aborted) return;
      const records = await api.completions(principal, plan, controller.signal);
      if (!records.some((row) => canonical(row) === canonical(accepted)))
        throw new StreamError();
      if (!alive.current || controller.signal.aborted) return;
      setRows(records);
      setPending(null);
      setMessage(
        "Session record saved and read back. The approved plan is unchanged.",
      );
    } catch (error) {
      if (!alive.current || controller.signal.aborted) return;
      if (
        error instanceof SubmissionFailure &&
        [
          "session_already_recorded",
          "idempotency_mismatch",
          "plan_mismatch",
          "not_found",
          "invalid_request",
        ].includes(error.error.code)
      ) {
        setPending(null);
        setLoaded(false);
        if (error.error.code === "plan_mismatch") {
          setBlocked(true);
          setMessage(
            "This saved plan identity does not match. Open the saved plan again.",
          );
        } else
          setMessage(
            "The submission conflicts or is unavailable. Reload session records before continuing.",
          );
      } else
        setMessage(
          "Submission is not confirmed. Retry the same submission; if you leave, read saved records before submitting again.",
        );
    } finally {
      if (alive.current && active.current === controller) {
        active.current = null;
        setBusy(false);
      }
    }
  }

  return (
    <section
      className="session-records"
      aria-label="Session completion and feedback"
    >
      <h3>Completion & feedback</h3>
      <p>
        Record a session only after your explicit action. Feedback is optional.
        Submitted records cannot be edited in this local workspace.
      </p>
      <p role="status">{message}</p>
      <button
        className="secondary"
        disabled={busy || pending !== null || blocked}
        onClick={() => void read()}
      >
        Reload session records
      </button>
      {pending && (
        <button disabled={busy} onClick={() => void submit(pending.day)}>
          Retry the same submission
        </button>
      )}
      {plan.plan.days.map((day) => {
        const record = rows.find((row) => row.day_index === day.day_index);
        const value = choices[day.day_index] ?? empty;
        const disabled = busy || !loaded || pending !== null || blocked;
        return (
          <article className="session" key={day.day_index}>
            <h4>Session {day.day_index} record</h4>
            {record ? (
              <p data-session-record={day.day_index}>
                Submitted: {record.status} · effort:{" "}
                {record.effort ?? "not provided"} · rating:{" "}
                {record.rating ?? "not provided"} · record revision{" "}
                {record.revision}
              </p>
            ) : (
              <form
                aria-label={`Record session ${day.day_index}`}
                onSubmit={(event) => {
                  event.preventDefault();
                  void submit(day.day_index);
                }}
              >
                <label>
                  Session {day.day_index} status
                  <select
                    aria-label={`Session ${day.day_index} status`}
                    value={value.status}
                    disabled={disabled}
                    onChange={(event) =>
                      change(day.day_index, "status", event.target.value)
                    }
                  >
                    <option value="">Choose a status</option>
                    <option value="completed">Completed</option>
                    <option value="partial">Partly completed</option>
                    <option value="skipped">Skipped</option>
                  </select>
                </label>
                <label>
                  Perceived effort (optional)
                  <select
                    aria-label={`Session ${day.day_index} effort`}
                    value={value.effort}
                    disabled={
                      disabled || !value.status || value.status === "skipped"
                    }
                    onChange={(event) =>
                      change(day.day_index, "effort", event.target.value)
                    }
                  >
                    <option value="">Not provided</option>
                    <option value="easy">Easy</option>
                    <option value="moderate">Moderate</option>
                    <option value="hard">Hard</option>
                  </select>
                </label>
                <label>
                  Session rating (optional, 1 lowest–5 highest)
                  <select
                    aria-label={`Session ${day.day_index} rating`}
                    value={value.rating}
                    disabled={
                      disabled || !value.status || value.status === "skipped"
                    }
                    onChange={(event) =>
                      change(day.day_index, "rating", event.target.value)
                    }
                  >
                    <option value="">Not provided</option>
                    {[1, 2, 3, 4, 5].map((rating) => (
                      <option key={rating} value={rating}>
                        {rating}
                      </option>
                    ))}
                  </select>
                </label>
                <button disabled={disabled || !value.status}>
                  Submit session {day.day_index} record
                </button>
              </form>
            )}
          </article>
        );
      })}
    </section>
  );
}
