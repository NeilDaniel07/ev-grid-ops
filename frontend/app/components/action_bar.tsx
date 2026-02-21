import { useMemo, useState } from "react";

import type { DispatchRequest, VerifyRequest } from "../lib/types";

export type WorkflowStage = 1 | 2 | 3 | 4 | 5;

type LoadingState = {
  baseline: boolean;
  certainty: boolean;
  dispatch: boolean;
  verify: boolean;
};

type ActionBarProps = {
  hasSelectedCase: boolean;
  selectedCaseId: string | null;
  loading: LoadingState;
  stage: WorkflowStage;
  onRunBaseline: () => Promise<void>;
  onRunCertainty: () => Promise<void>;
  onDispatch: (payload: DispatchRequest) => Promise<void>;
  onVerify: (payload: VerifyRequest) => Promise<void>;
};

const DEFAULT_TEAM = "FieldOps";

function toDueAtIso(hoursFromNow: number): string {
  const safeHours = Number.isFinite(hoursFromNow) ? Math.max(1, hoursFromNow) : 8;
  return new Date(Date.now() + safeHours * 60 * 60 * 1000).toISOString();
}

export function ActionBar({
  hasSelectedCase,
  selectedCaseId,
  loading,
  stage,
  onRunBaseline,
  onRunCertainty,
  onDispatch,
  onVerify,
}: ActionBarProps) {
  const [dispatchHours, setDispatchHours] = useState(8);
  const [dispatchState, setDispatchState] = useState<"created" | "in_progress" | "done">("created");
  const [verifyResult, setVerifyResult] = useState<"confirmed_issue" | "false_alarm" | "needs_more_data">(
    "confirmed_issue",
  );
  const [verifyNotes, setVerifyNotes] = useState("");

  const dispatchPayload = useMemo<DispatchRequest>(
    () => ({ assigned_team: DEFAULT_TEAM, due_at: toDueAtIso(dispatchHours), state: dispatchState }),
    [dispatchHours, dispatchState],
  );

  const verifyPayload = useMemo<VerifyRequest>(
    () => ({ result: verifyResult, notes: verifyNotes.trim() ? verifyNotes.trim() : undefined }),
    [verifyResult, verifyNotes],
  );

  return (
    <section className="panel actions">
      <div className="action-header">
        <h3>Actions</h3>
        <p className="muted">Selected case: {selectedCaseId ?? "none"}</p>
      </div>

      {stage === 1 ? (
        <div className="button-row">
          <button type="button" className="btn-primary" onClick={() => void onRunBaseline()} disabled={loading.baseline}>
            {loading.baseline ? "Running Baseline..." : "Step 1: Run Baseline"}
          </button>
        </div>
      ) : null}

      {stage === 2 ? (
        <div className="button-row">
          <button type="button" className="btn-primary" onClick={() => void onRunCertainty()} disabled={loading.certainty}>
            {loading.certainty ? "Running Certainty..." : "Step 2: Run Certainty"}
          </button>
        </div>
      ) : null}

      {stage >= 3 ? (
        <>
          <div className="button-row" style={{ marginBottom: 8 }}>
            <button
              type="button"
              className="btn-secondary"
              onClick={() => void onRunBaseline()}
              disabled={loading.baseline || loading.certainty}
            >
              {loading.baseline ? "Refreshing..." : "Refresh Baseline"}
            </button>
            <button
              type="button"
              className="btn-secondary"
              onClick={() => void onRunCertainty()}
              disabled={loading.baseline || loading.certainty}
            >
              {loading.certainty ? "Refreshing..." : "Refresh Certainty"}
            </button>
          </div>

          <div className="actions-grid">
            <div className="field-group stack">
              <h4>Dispatch</h4>

              <label>
                <span className="label">Due In (hours)</span>
                <input
                  type="number"
                  min={1}
                  step={1}
                  value={dispatchHours}
                  onChange={(event) => setDispatchHours(Number(event.target.value))}
                />
              </label>

              <label>
                <span className="label">State</span>
                <select
                  value={dispatchState}
                  onChange={(event) => setDispatchState(event.target.value as "created" | "in_progress" | "done")}
                >
                  <option value="created">created</option>
                  <option value="in_progress">in_progress</option>
                  <option value="done">done</option>
                </select>
              </label>

              <button
                type="button"
                className="btn-primary"
                onClick={() => void onDispatch(dispatchPayload)}
                disabled={!hasSelectedCase || loading.dispatch}
              >
                {loading.dispatch ? "Dispatching..." : "Dispatch Case"}
              </button>
            </div>

            <div className="field-group stack">
              <h4>Verification</h4>

              <label>
                <span className="label">Result</span>
                <select
                  value={verifyResult}
                  onChange={(event) =>
                    setVerifyResult(event.target.value as "confirmed_issue" | "false_alarm" | "needs_more_data")
                  }
                >
                  <option value="confirmed_issue">confirmed_issue</option>
                  <option value="false_alarm">false_alarm</option>
                  <option value="needs_more_data">needs_more_data</option>
                </select>
              </label>

              <label>
                <span className="label">Notes</span>
                <input
                  value={verifyNotes}
                  onChange={(event) => setVerifyNotes(event.target.value)}
                  placeholder="Optional verification notes"
                />
              </label>

              <button
                type="button"
                className="btn-primary"
                onClick={() => void onVerify(verifyPayload)}
                disabled={!hasSelectedCase || loading.verify}
              >
                {loading.verify ? "Submitting..." : "Submit Verification"}
              </button>
            </div>
          </div>
        </>
      ) : null}
    </section>
  );
}
