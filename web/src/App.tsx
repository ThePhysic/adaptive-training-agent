import { useEffect, useRef, useState } from "react";
import { BrowserApi, HttpFailure } from "./api.js";
import { CompletionPanel } from "./CompletionPanel.js";
import type {
  Exercise,
  Preferences,
  Principal,
  SavedProfile,
  TrainingApi,
  ApprovalRequest,
  SavedPlan,
} from "./api.js";
import { canonical, StreamError, planHash } from "./sse.js";
import type { Candidate, Plan, Terminal } from "./sse.js";

const defaultApi = new BrowserApi();
const initial: Preferences = {
  adult: false,
  goal: "general_strength",
  equipment: "bodyweight",
  experience: "beginner",
  days_per_week: 2,
  session_minutes: 20,
  excluded_ids: [],
  excluded_tags: [],
};
const stages = {
  context: "Reading saved preferences…",
  drafting: "Preparing your plan…",
  validating: "Checking the plan…",
  repairing: "Correcting the draft…",
};
const labels: Record<string, string> = {
  stale_profile: "Your saved profile changed. Reload it and generate again.",
  capacity_exceeded:
    "A generation is already running. Stop it or wait, then try again.",
  candidate_expired: "This preview expired. Generate a new plan.",
  candidate_superseded: "This preview was replaced. Generate a new plan.",
  candidate_mismatch:
    "This preview cannot be revised again. Generate a new plan.",
  revision_in_progress: "A revision is already running. Stop it or wait.",
  budget_exceeded: "The request reached its limit. Generate again when ready.",
  provider_failure:
    "The draft could not be completed. Generate again when ready.",
  invalid_request: "Choose supported preferences and try again.",
  unauthorized:
    "This workspace requires authorized localhost development access.",
  not_found:
    "The saved item is unavailable. Reload your profile or generate again.",
  candidate_already_approved:
    "This candidate was already approved. Check saved plans.",
  idempotency_mismatch:
    "The approval key conflicts with a different request. Check saved plans before starting again.",
  reconciliation_pending:
    "Approval is still being reconciled. Retry with the same key; do not submit a new approval.",
};
function failureMessage(error: unknown) {
  return error instanceof HttpFailure
    ? (labels[error.error.code] ?? "The request could not be completed.")
    : "Stream incomplete or invalid. Generate again.";
}
type Review = { plan: Plan; candidate: Candidate };
type Attempt = {
  request: ApprovalRequest;
  plan: Plan;
  profileRevision: number;
};

export function App({ api = defaultApi }: { api?: TrainingApi }) {
  const [principal, setPrincipal] = useState<Principal>("synthetic-a");
  const [preferences, setPreferences] = useState<Preferences>(initial);
  const [saved, setSaved] = useState<SavedProfile | null>(null);
  const [catalog, setCatalog] = useState<Exercise[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [saving, setSaving] = useState(false);
  const [text, setText] = useState("");
  const [message, setMessage] = useState("Loading local profile…");
  const [preview, setPreview] = useState<Plan | null>(null);
  const [terminal, setTerminal] = useState<Terminal | null>(null);
  const [base, setBase] = useState<Review | null>(null);
  const [approving, setApproving] = useState(false);
  const [attempt, setAttempt] = useState<Attempt | null>(null);
  const [durable, setDurable] = useState<SavedPlan | null>(null);
  const [history, setHistory] = useState<SavedPlan[]>([]);
  const [historyMore, setHistoryMore] = useState(false);
  const [reading, setReading] = useState(false);
  const active = useRef<AbortController | null>(null);
  const epoch = useRef(0);
  const [reload, setReload] = useState(0);
  const dirty =
    !saved || canonical(preferences) !== canonical(saved.preferences);

  function invalidate() {
    epoch.current++;
    active.current?.abort();
    active.current = null;
    setBusy(false);
    setSaving(false);
    setPreview(null);
    setTerminal(null);
    setBase(null);
    setApproving(false);
    setReading(false);
    setAttempt(null);
    setDurable(null);
  }
  useEffect(() => {
    const controller = new AbortController();
    const current = ++epoch.current;
    setLoading(true);
    setHistory([]);
    setHistoryMore(false);
    setDurable(null);
    setAttempt(null);
    setSaved(null);
    setPreview(null);
    setTerminal(null);
    setBase(null);
    setText("");
    setPreferences(initial);
    setMessage("Loading local profile…");
    Promise.all([
      api.profile(principal, controller.signal),
      api.catalog(principal, controller.signal),
      api.history(principal, controller.signal),
    ])
      .then(([profile, records, rows]) => {
        if (controller.signal.aborted || current !== epoch.current) return;
        setSaved(profile);
        setPreferences(profile?.preferences ?? initial);
        setCatalog(records);
        setHistory(rows);
        setHistoryMore(rows.length === 5);
        setMessage(
          profile
            ? "Saved preferences loaded. Ready to generate."
            : "Choose synthetic preferences and Save to begin.",
        );
      })
      .catch((error) => {
        if (!controller.signal.aborted && current === epoch.current)
          setMessage(failureMessage(error));
      })
      .finally(() => {
        if (!controller.signal.aborted && current === epoch.current)
          setLoading(false);
      });
    return () => {
      controller.abort();
      active.current?.abort();
      epoch.current++;
    };
  }, [api, principal, reload]);

  function change<K extends keyof Preferences>(key: K, value: Preferences[K]) {
    invalidate();
    setPreferences((current) => ({ ...current, [key]: value }));
    setMessage("Unsaved changes. Save before generating.");
  }
  async function save() {
    if (
      loading ||
      busy ||
      saving ||
      approving ||
      reading ||
      attempt ||
      !preferences.adult
    )
      return;
    invalidate();
    const current = epoch.current;
    const controller = new AbortController();
    active.current = controller;
    setSaving(true);
    setMessage("Saving preferences…");
    try {
      const profile = await api.save(
        principal,
        preferences,
        saved?.revision ?? 0,
        controller.signal,
      );
      if (controller.signal.aborted || current !== epoch.current) return;
      setSaved(profile);
      setPreferences(profile.preferences);
      setMessage("Preferences saved. Ready to generate.");
    } catch (error) {
      if (!controller.signal.aborted && current === epoch.current)
        setMessage(failureMessage(error));
    } finally {
      if (current === epoch.current) {
        setSaving(false);
        active.current = null;
      }
    }
  }
  async function generate(revise = false) {
    if (
      !saved ||
      dirty ||
      loading ||
      saving ||
      approving ||
      reading ||
      attempt ||
      active.current ||
      (revise && (!base || base.candidate.revision !== 1))
    )
      return;
    const original = revise ? base : null;
    const current = ++epoch.current;
    const controller = new AbortController();
    active.current = controller;
    setBusy(true);
    setPreview(null);
    setTerminal(null);
    setDurable(null);
    setAttempt(null);
    if (!revise) setBase(null);
    setMessage(revise ? "Revising your preview…" : "Starting generation…");
    try {
      const result = await api.generate(
        principal,
        { profile_revision: saved.revision, preferences_text: text },
        controller.signal,
        (event) => {
          if (controller.signal.aborted || current !== epoch.current) return;
          if (event.event_type === "status")
            setMessage(stages[event.payload.stage]);
          if (event.event_type === "draft") {
            setPreview(event.payload);
            setMessage("Validated draft received. Waiting for completion…");
          }
          if (event.event_type === "error") {
            setPreview(null);
            setMessage(labels[event.payload.code] ?? "Generation failed.");
          }
        },
        original?.candidate,
      );
      if (controller.signal.aborted || current !== epoch.current) return;
      setTerminal(result.done);
      if (result.done.outcome === "plan") {
        if (!result.draft) throw new StreamError();
        setPreview(result.draft);
        setBase({ plan: result.draft, candidate: result.done.candidate });
        setMessage("Complete preview received. Review each session below.");
      } else {
        setPreview(null);
        setMessage(
          result.done.outcome === "clarify"
            ? "Choose supported preferences before continuing."
            : result.done.outcome === "abstain"
              ? "No plan was generated for this request."
              : (labels[result.done.error.code] ?? "Generation failed."),
        );
        if (
          result.done.outcome === "error" &&
          [
            "stale_profile",
            "candidate_expired",
            "candidate_superseded",
            "candidate_mismatch",
          ].includes(result.done.error.code)
        )
          setBase(null);
      }
    } catch (error) {
      if (controller.signal.aborted || current !== epoch.current) return;
      setPreview(null);
      setTerminal(null);
      setMessage(failureMessage(error));
      if (
        error instanceof HttpFailure &&
        [
          "stale_profile",
          "candidate_expired",
          "candidate_superseded",
          "candidate_mismatch",
        ].includes(error.error.code)
      )
        setBase(null);
    } finally {
      if (current === epoch.current) {
        setBusy(false);
        active.current = null;
      }
    }
  }
  function stop() {
    if (!busy || !active.current) return;
    epoch.current++;
    active.current.abort();
    active.current = null;
    setBusy(false);
    setPreview(null);
    setTerminal(null);
    setMessage(
      "Stopped. The incomplete preview was cleared. No automatic retry.",
    );
  }
  function switchPrincipal(value: Principal) {
    invalidate();
    setCatalog([]);
    setPrincipal(value);
  }

  async function approve() {
    if (
      active.current ||
      !base ||
      !preview ||
      terminal?.outcome !== "plan" ||
      dirty ||
      durable ||
      canonical(base.candidate) !== canonical(terminal.candidate) ||
      canonical(preview) !== canonical(base.plan)
    )
      return;
    const current = ++epoch.current;
    const controller = new AbortController();
    active.current = controller;
    setApproving(true);
    setMessage(
      attempt
        ? "Recovering approval with the same key…"
        : "Saving your approved plan…",
    );
    let confirmed = false;
    let sent = attempt !== null;
    try {
      if ((await planHash(preview)) !== base.candidate.content_hash)
        throw new StreamError();
      if (controller.signal.aborted || current !== epoch.current) return;
      const pending = attempt ?? {
        request: { ...base.candidate, idempotency_key: crypto.randomUUID() },
        plan: base.plan,
        profileRevision: saved!.revision,
      };
      setAttempt(pending);
      sent = true;
      const approval = await api.approve(
        principal,
        pending.request,
        controller.signal,
      );
      if (
        approval.candidate.candidate_id !== pending.request.candidate_id ||
        approval.candidate.revision !== pending.request.revision ||
        approval.candidate.content_hash !== pending.request.content_hash
      )
        throw new StreamError();
      confirmed = true;
      if (controller.signal.aborted || current !== epoch.current) return;
      const row = await api.plan(
        principal,
        approval.plan_id,
        controller.signal,
      );
      if (
        canonical(row.approval) !== canonical(approval) ||
        canonical(row.plan) !== canonical(pending.plan) ||
        row.versions.profile_revision !== pending.profileRevision ||
        row.approval.candidate.content_hash !== pending.request.content_hash
      )
        throw new StreamError();
      if (controller.signal.aborted || current !== epoch.current) return;
      setDurable(row);
      setAttempt(null);
      setBase(null);
      setMessage("Approved & saved. Showing the durable database snapshot.");
      try {
        const rows = await api.history(principal, controller.signal);
        if (current === epoch.current && !controller.signal.aborted) {
          setHistory(rows);
          setHistoryMore(rows.length === 5);
        }
      } catch {
        /* Durable readback remains valid; history has an explicit refresh. */
      }
    } catch (error) {
      if (controller.signal.aborted || current !== epoch.current) return;
      if (!sent) {
        setBase(null);
        setPreview(null);
        setTerminal(null);
        setAttempt(null);
        setMessage(
          "The reviewed preview no longer matches its identity. Generate again.",
        );
        return;
      }
      const conflict =
        error instanceof HttpFailure &&
        [
          "candidate_expired",
          "candidate_superseded",
          "candidate_mismatch",
          "candidate_already_approved",
          "stale_profile",
          "idempotency_mismatch",
          "not_found",
        ].includes(error.error.code);
      if (conflict) {
        setAttempt(null);
        setBase(null);
        setTerminal(null);
        setPreview(null);
        setMessage(failureMessage(error));
      } else if (
        error instanceof HttpFailure &&
        error.error.code === "reconciliation_pending"
      ) {
        setMessage(labels.reconciliation_pending);
      } else {
        setMessage(
          confirmed
            ? "Approval committed, but readback was interrupted. Retry approval with the same key."
            : "Approval outcome is not confirmed. Retry approval uses the same key; check saved plans if you leave this page.",
        );
      }
    } finally {
      if (current === epoch.current) {
        setApproving(false);
        active.current = null;
      }
    }
  }

  async function readHistory(more = false) {
    if (active.current) return;
    const current = ++epoch.current;
    const controller = new AbortController();
    active.current = controller;
    setReading(true);
    try {
      const rows = await api.history(
        principal,
        controller.signal,
        more ? history.at(-1)?.approval.plan_id : undefined,
      );
      if (current !== epoch.current || controller.signal.aborted) return;
      setHistory((prior) => (more ? [...prior, ...rows] : rows));
      setHistoryMore(rows.length === 5);
    } catch (error) {
      if (current === epoch.current && !controller.signal.aborted)
        setMessage(failureMessage(error));
    } finally {
      if (current === epoch.current) {
        setReading(false);
        active.current = null;
      }
    }
  }

  async function openSaved(planId: string) {
    if (active.current || attempt) return;
    invalidate();
    const current = epoch.current;
    const controller = new AbortController();
    active.current = controller;
    setReading(true);
    try {
      const row = await api.plan(principal, planId, controller.signal);
      if (current !== epoch.current || controller.signal.aborted) return;
      setDurable(row);
      setPreview(row.plan);
      setMessage("Approved & saved. Showing the durable database snapshot.");
    } catch (error) {
      if (current === epoch.current && !controller.signal.aborted)
        setMessage(failureMessage(error));
    } finally {
      if (current === epoch.current) {
        setReading(false);
        active.current = null;
      }
    }
  }
  const tags = [
    ...new Set(catalog.flatMap((record) => record.exclusion_tags)),
  ].sort();
  const disabled = loading || busy || saving || approving || reading;
  const complete = terminal?.outcome === "plan" || durable !== null;

  return (
    <main>
      <header className="masthead">
        <div>
          <p className="eyebrow">LOCAL TRAINING WORKSPACE</p>
          <h1>
            Make room for <em>your next session.</em>
          </h1>
          <p className="intro">
            Choose your preferences. Review a structured weekly preview. Keep
            every decision explicit.
          </p>
        </div>
        <label className="identity">
          Synthetic profile
          <select
            aria-label="Synthetic profile"
            value={principal}
            onChange={(e) => switchPrincipal(e.target.value as Principal)}
          >
            <option value="synthetic-a">Local profile A</option>
            <option value="synthetic-b">Local profile B</option>
          </select>
        </label>
      </header>
      <p className="notice">
        Synthetic adult wellness planning only. Do not enter personal or medical
        information. Previews are deterministic and are not saved plans.
      </p>
      <div className="workspace">
        <section className="card preferences">
          <div className="section-heading">
            <span className="step">01</span>
            <div>
              <p className="eyebrow">YOUR STARTING POINT</p>
              <h2>Training preferences</h2>
            </div>
          </div>
          <fieldset disabled={disabled || attempt !== null}>
            <legend className="sr-only">Supported training preferences</legend>
            <label>
              Goal
              <select
                value={preferences.goal}
                onChange={(e) =>
                  change("goal", e.target.value as Preferences["goal"])
                }
              >
                <option value="general_strength">General strength</option>
                <option value="general_conditioning">
                  General conditioning
                </option>
              </select>
            </label>
            <label>
              Equipment
              <select
                value={preferences.equipment}
                onChange={(e) =>
                  change(
                    "equipment",
                    e.target.value as Preferences["equipment"],
                  )
                }
              >
                <option value="bodyweight">Bodyweight</option>
                <option value="dumbbells_and_bodyweight">
                  Dumbbells + bodyweight
                </option>
              </select>
            </label>
            <label>
              Experience
              <select
                value={preferences.experience}
                onChange={(e) =>
                  change(
                    "experience",
                    e.target.value as Preferences["experience"],
                  )
                }
              >
                <option value="beginner">Beginner</option>
                <option value="intermediate">Intermediate</option>
              </select>
            </label>
            <div className="pair">
              <label>
                Days per week
                <select
                  value={preferences.days_per_week}
                  onChange={(e) =>
                    change(
                      "days_per_week",
                      Number(e.target.value) as Preferences["days_per_week"],
                    )
                  }
                >
                  {[2, 3, 4].map((n) => (
                    <option key={n} value={n}>
                      {n} days
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Session preset
                <select
                  value={preferences.session_minutes}
                  onChange={(e) =>
                    change(
                      "session_minutes",
                      Number(e.target.value) as Preferences["session_minutes"],
                    )
                  }
                >
                  {[20, 30, 45].map((n) => (
                    <option key={n} value={n}>
                      {n} minutes
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <details>
              <summary>Exclude exercises or movement tags</summary>
              <p className="hint">
                Up to 12 exercises and 8 catalog tags. Exclusions are always
                respected.
              </p>
              <div className="exclusions">
                {catalog.map((record) => (
                  <label key={record.exercise_id} className="check">
                    <input
                      type="checkbox"
                      checked={
                        preferences.excluded_ids?.includes(
                          record.exercise_id,
                        ) ?? false
                      }
                      disabled={
                        !preferences.excluded_ids?.includes(
                          record.exercise_id,
                        ) && (preferences.excluded_ids?.length ?? 0) >= 12
                      }
                      onChange={(e) =>
                        change(
                          "excluded_ids",
                          e.target.checked
                            ? [
                                ...(preferences.excluded_ids ?? []),
                                record.exercise_id,
                              ]
                            : (preferences.excluded_ids ?? []).filter(
                                (id) => id !== record.exercise_id,
                              ),
                        )
                      }
                    />
                    {record.title}
                  </label>
                ))}
              </div>
              <div className="tags">
                {tags.map((tag) => (
                  <label key={tag} className="check">
                    <input
                      type="checkbox"
                      checked={
                        preferences.excluded_tags?.includes(tag) ?? false
                      }
                      disabled={
                        !preferences.excluded_tags?.includes(tag) &&
                        (preferences.excluded_tags?.length ?? 0) >= 8
                      }
                      onChange={(e) =>
                        change(
                          "excluded_tags",
                          e.target.checked
                            ? [...(preferences.excluded_tags ?? []), tag]
                            : (preferences.excluded_tags ?? []).filter(
                                (t) => t !== tag,
                              ),
                        )
                      }
                    />
                    {tag.replaceAll("_", " ")}
                  </label>
                ))}
              </div>
            </details>
            <label className="check attestation">
              <input
                type="checkbox"
                checked={preferences.adult}
                onChange={(e) => change("adult", e.target.checked)}
              />
              I am using synthetic preferences for an adult aged 18 or older.
            </label>
          </fieldset>
          <div className="actions">
            <button
              onClick={() => void save()}
              disabled={
                disabled || attempt !== null || !preferences.adult || !dirty
              }
            >
              {saving ? "Saving…" : "Save profile"}
            </button>
            <button
              className="secondary"
              disabled={disabled || attempt !== null}
              onClick={() => {
                invalidate();
                setReload((n) => n + 1);
              }}
            >
              Reload saved profile
            </button>
          </div>
          <p className="hint">
            {saved
              ? `Saved revision ${saved.revision}${dirty ? " · unsaved changes" : " · up to date"}`
              : "No saved profile yet"}
          </p>
        </section>
        <section className="card review">
          <div className="section-heading">
            <span className="step">02</span>
            <div>
              <p className="eyebrow">BUILD, THEN REVIEW</p>
              <h2>Your weekly preview</h2>
            </div>
            <span className="badge">
              {durable
                ? "APPROVED & SAVED"
                : complete
                  ? "COMPLETE PREVIEW"
                  : "NOT SAVED"}
            </span>
          </div>
          <label>
            Optional general preference
            <textarea
              maxLength={2048}
              disabled={disabled || attempt !== null}
              value={text}
              onChange={(e) => {
                setText(e.target.value);
                setPreview(null);
                setTerminal(null);
              }}
              placeholder="Free text requires clarification here. Save supported changes in your profile."
            />
          </label>
          <div className="actions">
            <button
              disabled={disabled || attempt !== null || !saved || dirty}
              onClick={() => void generate()}
            >
              Generate preview
            </button>
            <button
              className="secondary"
              disabled={
                disabled ||
                attempt !== null ||
                !base ||
                base.candidate.revision !== 1 ||
                dirty
              }
              onClick={() => void generate(true)}
            >
              Revise once
            </button>
            <button className="stop" disabled={!busy} onClick={stop}>
              Stop
            </button>
          </div>
          <p className="status" role="status" aria-live="polite">
            <span className={busy ? "dot active" : "dot"} />
            {message}
          </p>
          {terminal?.outcome === "clarify" && (
            <div className="outcome">
              <h3>A choice is needed</h3>
              <ul>
                {terminal.choices.map((choice) => (
                  <li key={choice}>{choice}</li>
                ))}
              </ul>
              <p>
                Update the supported preferences, Save, then generate again.
              </p>
            </div>
          )}
          {terminal?.outcome === "abstain" && (
            <div className="outcome">
              <h3>No supported plan</h3>
              <p>
                {terminal.reason === "medical_context"
                  ? "Requests involving medical or rehabilitation needs require qualified professional advice."
                  : "Change the supported preferences or exclusions before trying again."}
              </p>
            </div>
          )}
          {preview ? (
            <PlanReview
              plan={preview}
              catalog={
                durable &&
                durable.versions.catalog_revision !==
                  catalog[0]?.catalog_revision
                  ? []
                  : catalog
              }
              complete={complete}
              approved={durable !== null}
            />
          ) : (
            <div className="empty">
              <span className="empty-mark" aria-hidden="true">
                ↗
              </span>
              <h3>A clear plan starts with a few choices.</h3>
              <p>
                Save your preferences, then generate a preview to review every
                session.
              </p>
            </div>
          )}
          <div className="approval">
            <button
              disabled={
                disabled ||
                !base ||
                terminal?.outcome !== "plan" ||
                !complete ||
                dirty ||
                durable !== null
              }
              onClick={() => void approve()}
            >
              {approving
                ? "Saving approval…"
                : attempt
                  ? "Retry approval"
                  : "Approve & save"}
            </button>
            {durable ? (
              <p className="saved" role="note">
                Approved &amp; saved · profile revision{" "}
                {durable.versions.profile_revision} · catalog{" "}
                {durable.versions.catalog_revision}. This is the stored
                snapshot.
              </p>
            ) : (
              <p>
                Approval is an explicit durable Save. It may finish after a
                connection is lost. Retries reuse the same key while this page
                remains open.
              </p>
            )}
          </div>
          {durable && (
            <CompletionPanel
              key={`${principal}:${durable.approval.plan_id}`}
              api={api}
              principal={principal}
              plan={durable}
            />
          )}
          <section className="history" aria-label="Saved plans">
            <h3>Saved plans</h3>
            <div className="actions">
              <button
                className="secondary"
                disabled={disabled}
                onClick={() => void readHistory()}
              >
                Refresh saved plans
              </button>
              {historyMore && (
                <button
                  className="secondary"
                  disabled={disabled}
                  onClick={() => void readHistory(true)}
                >
                  Load more saved plans
                </button>
              )}
            </div>
            {history.length === 0 ? (
              <p className="hint">No approved plans for this local profile.</p>
            ) : (
              <ul>
                {history.map((row) => (
                  <li key={row.approval.plan_id}>
                    <span>
                      {row.plan.profile.days_per_week} sessions ·{" "}
                      {row.plan.profile.session_minutes} min preset · saved
                      profile revision {row.versions.profile_revision}
                    </span>
                    <button
                      className="secondary"
                      disabled={disabled || attempt !== null}
                      onClick={() => void openSaved(row.approval.plan_id)}
                    >
                      Open saved plan
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </section>
      </div>
      <footer>
        LOCAL &amp; SYNTHETIC{" "}
        <span>
          Approved plans persist locally. Unapproved previews expire or
          disappear on restart.
        </span>
      </footer>
    </main>
  );
}

export function PlanReview({
  plan,
  catalog,
  complete,
  approved = false,
}: {
  plan: Plan;
  catalog: Exercise[];
  complete: boolean;
  approved?: boolean;
}) {
  return (
    <div className="plan" data-complete={complete}>
      <h3>
        {approved
          ? "Saved plan snapshot"
          : complete
            ? "Ready for your review"
            : "Draft preview · waiting for completion"}
      </h3>
      <p className="hint">
        Requested preset: {plan.profile.session_minutes} minutes ·{" "}
        {plan.profile.days_per_week} sessions. Times are estimates, including
        warm-up, cooldown and transitions.
      </p>
      {plan.days.map((day) => (
        <article className="session" key={day.day_index}>
          <div className="day-heading">
            <h4>Session {day.day_index}</h4>
            <span>
              {(day.planned_seconds / 60).toFixed(1)} min estimated{" "}
              <small>({day.planned_seconds} s)</small>
            </span>
          </div>
          <ol>
            {day.blocks.map((block) => (
              <li key={block.exercise_id}>
                <strong>
                  {catalog.find((r) => r.exercise_id === block.exercise_id)
                    ?.title ?? block.exercise_id}
                </strong>
                <span>
                  {block.sets} sets ×{" "}
                  {block.mode === "repetitions"
                    ? `${block.repetitions_per_set} reps`
                    : `${block.work_seconds_per_set} s work`}{" "}
                  · {block.rest_between_sets_seconds} s rest between sets
                </span>
              </li>
            ))}
          </ol>
        </article>
      ))}
    </div>
  );
}
