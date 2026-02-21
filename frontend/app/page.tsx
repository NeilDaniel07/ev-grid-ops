"use client";

import { useEffect, useMemo, useState } from "react";

import { ActionBar, type WorkflowStage } from "./components/action_bar";
import { CaseDetail } from "./components/case_detail";
import { CaseMap } from "./components/case_map";
import { CaseQueue } from "./components/case_queue";
import { KpiCards } from "./components/kpi_cards";
import { dispatchCase, getCases, getCompareMetrics, runBaseline, runCertainty, verifyCase } from "./lib/api";
import type {
  Case,
  CaseMode,
  CompareMetrics,
  DispatchRequest,
  Signal,
  VerificationTask,
  VerifyRequest,
} from "./lib/types";

type LoadingState = {
  baseline: boolean;
  certainty: boolean;
  dispatch: boolean;
  verify: boolean;
  metrics: boolean;
};

type Selection = { mode: CaseMode; caseId: string } | null;

const DEMO_SIGNALS: Signal[] = [
  {
    id: "sig_001",
    source: "311",
    timestamp: "2026-02-20T20:00:00Z",
    charger_id: "AUS_0123",
    lat: 30.2672,
    lon: -97.7431,
    status: "down",
    text: "charger dead",
  },
  {
    id: "sig_002",
    source: "ugc",
    timestamp: "2026-02-20T20:05:00Z",
    charger_id: "AUS_0123",
    lat: 30.2672,
    lon: -97.7431,
    status: "down",
    text: "connector not working",
  },
  {
    id: "sig_003",
    source: "charger_api",
    timestamp: "2026-02-20T20:08:00Z",
    charger_id: "AUS_0123",
    lat: 30.2672,
    lon: -97.7431,
    status: "degraded",
    text: "session start failures",
  },
  {
    id: "sig_004",
    source: "311",
    timestamp: "2026-02-20T20:10:00Z",
    charger_id: "AUS_0450",
    lat: 30.269,
    lon: -97.749,
    status: "unknown",
    text: "payment terminal issue",
  },
  {
    id: "sig_005",
    source: "charger_api",
    timestamp: "2026-02-20T20:12:00Z",
    charger_id: "AUS_0450",
    lat: 30.269,
    lon: -97.749,
    status: "online",
    text: "heartbeat online",
  },
];

const STEP_LABELS: Record<WorkflowStage, string> = {
  1: "Run baseline triage",
  2: "Run certainty triage",
  3: "Select a case to review",
  4: "Take action (dispatch or verify)",
  5: "Workflow complete",
};

const STEP_HINTS: Record<WorkflowStage, string> = {
  1: "Start with baseline ranking to create an initial queue.",
  2: "Now run certainty to find ambiguous cases before dispatch.",
  3: "Click a case in either queue to open explanation and evidence.",
  4: "Dispatch clear issues or submit verification for uncertain ones.",
  5: "You can refresh triage anytime to process new signals.",
};

export default function Page() {
  const [baselineCases, setBaselineCases] = useState<Case[]>([]);
  const [certaintyCases, setCertaintyCases] = useState<Case[]>([]);
  const [verificationTasks, setVerificationTasks] = useState<VerificationTask[]>([]);
  const [metrics, setMetrics] = useState<CompareMetrics | null>(null);
  const [selection, setSelection] = useState<Selection>(null);
  const [hasActionTaken, setHasActionTaken] = useState(false);
  const [loading, setLoading] = useState<LoadingState>({
    baseline: false,
    certainty: false,
    dispatch: false,
    verify: false,
    metrics: false,
  });
  const [actionError, setActionError] = useState<string | null>(null);
  const [metricsError, setMetricsError] = useState<string | null>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const selectedCase = useMemo(() => {
    if (!selection) return null;
    const pool = selection.mode === "baseline" ? baselineCases : certaintyCases;
    return pool.find((item) => item.id === selection.caseId) ?? null;
  }, [selection, baselineCases, certaintyCases]);

  const selectedTask = useMemo(() => {
    if (!selectedCase) return null;
    return verificationTasks.find((task) => task.case_id === selectedCase.id) ?? null;
  }, [selectedCase, verificationTasks]);

  const selectedCaseId = selectedCase?.id ?? null;
  const locationIndex = useMemo(() => {
    const map: Record<string, { charger_id: string; lat: number; lon: number }> = {};
    for (const signal of DEMO_SIGNALS) {
      if (!map[signal.charger_id]) {
        map[signal.charger_id] = {
          charger_id: signal.charger_id,
          lat: signal.lat,
          lon: signal.lon,
        };
      }
    }
    return map;
  }, []);

  const workflowStage: WorkflowStage = useMemo(() => {
    if (baselineCases.length === 0) return 1;
    if (certaintyCases.length === 0) return 2;
    if (!selectedCase) return 3;
    if (!hasActionTaken) return 4;
    return 5;
  }, [baselineCases.length, certaintyCases.length, selectedCase, hasActionTaken]);

  useEffect(() => {
    void refreshMetrics();
  }, []);

  async function refreshMetrics() {
    setLoading((prev) => ({ ...prev, metrics: true }));
    setMetricsError(null);
    try {
      setMetrics(await getCompareMetrics());
    } catch (error) {
      setMetricsError(error instanceof Error ? error.message : "Failed to load metrics");
    } finally {
      setLoading((prev) => ({ ...prev, metrics: false }));
    }
  }

  function selectFirstCaseIfNeeded(mode: CaseMode, cases: Case[]) {
    if (cases.length === 0) return;
    setSelection((prev) => {
      if (!prev || prev.mode !== mode) return { mode, caseId: cases[0].id };
      return cases.some((item) => item.id === prev.caseId) ? prev : { mode, caseId: cases[0].id };
    });
  }

  async function handleRunBaseline() {
    setLoading((prev) => ({ ...prev, baseline: true }));
    setActionError(null);
    setActionMessage(null);

    try {
      const triageResult = await runBaseline(DEMO_SIGNALS);
      let cases = triageResult.cases;
      try {
        cases = (await getCases("baseline")).cases;
      } catch {
        // Use direct triage response if persistence route is not populated.
      }
      setBaselineCases(cases);
      setHasActionTaken(false);
      selectFirstCaseIfNeeded("baseline", cases);
      setActionMessage(`Baseline triage complete: ${cases.length} case(s).`);
      await refreshMetrics();
    } catch (error) {
      setActionError(error instanceof Error ? error.message : "Failed to run baseline triage");
    } finally {
      setLoading((prev) => ({ ...prev, baseline: false }));
    }
  }

  async function handleRunCertainty() {
    setLoading((prev) => ({ ...prev, certainty: true }));
    setActionError(null);
    setActionMessage(null);

    try {
      const triageResult = await runCertainty(DEMO_SIGNALS);
      let cases = triageResult.cases;
      try {
        cases = (await getCases("certainty")).cases;
      } catch {
        // Use direct triage response if persistence route is not populated.
      }
      setCertaintyCases(cases);
      setVerificationTasks(triageResult.verification_tasks);
      setHasActionTaken(false);
      selectFirstCaseIfNeeded("certainty", cases);
      setActionMessage(
        `Certainty triage complete: ${cases.length} case(s), ${triageResult.verification_tasks.length} verification task(s).`,
      );
      await refreshMetrics();
    } catch (error) {
      setActionError(error instanceof Error ? error.message : "Failed to run certainty triage");
    } finally {
      setLoading((prev) => ({ ...prev, certainty: false }));
    }
  }

  async function handleDispatch(payload: DispatchRequest) {
    if (!selectedCase) {
      setActionError("Select a case before dispatching.");
      return;
    }

    setLoading((prev) => ({ ...prev, dispatch: true }));
    setActionError(null);
    setActionMessage(null);

    try {
      await dispatchCase(selectedCase.id, payload);
      setHasActionTaken(true);
      setActionMessage(`Dispatch created for ${selectedCase.id}.`);
      if (selection) {
        const updated = await getCases(selection.mode);
        if (selection.mode === "baseline") setBaselineCases(updated.cases);
        else setCertaintyCases(updated.cases);
      }
      await refreshMetrics();
    } catch (error) {
      setActionError(error instanceof Error ? error.message : "Failed to dispatch case");
    } finally {
      setLoading((prev) => ({ ...prev, dispatch: false }));
    }
  }

  async function handleVerify(payload: VerifyRequest) {
    if (!selectedCase) {
      setActionError("Select a case before submitting verification.");
      return;
    }

    setLoading((prev) => ({ ...prev, verify: true }));
    setActionError(null);
    setActionMessage(null);

    try {
      const response = await verifyCase(selectedCase.id, payload);
      setHasActionTaken(true);
      setVerificationTasks((prev) => {
        const filtered = prev.filter((task) => task.case_id !== selectedCase.id);
        return [...filtered, response.verification_task];
      });
      setActionMessage(`Verification submitted for ${selectedCase.id}.`);
      try {
        setCertaintyCases((await getCases("certainty")).cases);
      } catch {
        // Keep local certainty state if readback route is unavailable.
      }
      await refreshMetrics();
    } catch (error) {
      setActionError(error instanceof Error ? error.message : "Failed to submit verification");
    } finally {
      setLoading((prev) => ({ ...prev, verify: false }));
    }
  }

  return (
    <main className="shell">
      <header className="hero">
        <h1>EV Reliability Copilot</h1>
        <p>Compare baseline triage vs certainty-aware triage and route uncertain cases to verification.</p>
      </header>

      <section className="panel workflow" aria-label="Guided workflow">
        <div className="workflow-head">
          <p className="workflow-label">Workflow Step {workflowStage} of 5</p>
          <p className="workflow-title">{STEP_LABELS[workflowStage]}</p>
          <p className="muted">{STEP_HINTS[workflowStage]}</p>
        </div>
        <div className="workflow-steps">
          {[1, 2, 3, 4, 5].map((step) => (
            <span
              key={step}
              className={`workflow-step ${step === workflowStage ? "active" : ""} ${step < workflowStage ? "done" : ""}`}
            >
              {step}
            </span>
          ))}
        </div>
      </section>

      <ActionBar
        hasSelectedCase={Boolean(selectedCase)}
        selectedCaseId={selectedCaseId}
        stage={workflowStage}
        loading={{
          baseline: loading.baseline,
          certainty: loading.certainty,
          dispatch: loading.dispatch,
          verify: loading.verify,
        }}
        onRunBaseline={handleRunBaseline}
        onRunCertainty={handleRunCertainty}
        onDispatch={handleDispatch}
        onVerify={handleVerify}
      />

      {actionError ? <p className="alert error">Action error: {actionError}</p> : null}
      {actionMessage ? <p className="alert success">{actionMessage}</p> : null}

      <KpiCards metrics={metrics} isLoading={loading.metrics} error={metricsError} />

      <section className="queues">
        <CaseQueue
          title="Baseline Queue"
          mode="baseline"
          cases={baselineCases}
          selectedCaseId={selection?.mode === "baseline" ? selection.caseId : null}
          isLoading={loading.baseline}
          onSelectCase={(mode, caseId) => setSelection({ mode, caseId })}
        />
        <CaseQueue
          title="Certainty Queue"
          mode="certainty"
          cases={certaintyCases}
          selectedCaseId={selection?.mode === "certainty" ? selection.caseId : null}
          isLoading={loading.certainty}
          onSelectCase={(mode, caseId) => setSelection({ mode, caseId })}
        />
      </section>

      <CaseMap
        cases={baselineCases}
        selectedCaseId={selectedCaseId}
        locationIndex={locationIndex}
        onSelectCase={(mode, caseId) => setSelection({ mode, caseId })}
      />

      <CaseDetail selectedCase={selectedCase} selectedMode={selection?.mode ?? null} verificationTask={selectedTask} />
    </main>
  );
}
