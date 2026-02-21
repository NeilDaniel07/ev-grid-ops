"use client";

import { useEffect, useMemo, useState } from "react";

import { ActionBar, type WorkflowStage } from "./components/action_bar";
import { CaseDetail } from "./components/case_detail";
import { CaseMap } from "./components/case_map";
import { CaseQueue } from "./components/case_queue";
import { KpiCards } from "./components/kpi_cards";
import { dispatchCase, getCases, getCompareMetrics, verifyCase } from "./lib/api";
import type {
  Case,
  CaseMode,
  CompareMetrics,
  DispatchRequest,
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
type CaseStatusMap = Record<
  string,
  {
    dispatched?: boolean;
    verified?: boolean;
    verificationResult?: "confirmed_issue" | "false_alarm" | "needs_more_data";
  }
>;

const STEP_LABELS: Record<WorkflowStage, string> = {
  1: "Load baseline queue",
  2: "Load certainty queue",
  3: "Select a case to review",
  4: "Take action (dispatch or verify)",
  5: "Workflow complete",
};

const STEP_HINTS: Record<WorkflowStage, string> = {
  1: "Start by loading the current baseline queue from backend.",
  2: "Now load certainty results to find ambiguous cases before dispatch.",
  3: "Click a case in either queue to open explanation and evidence.",
  4: "Dispatch clear issues or submit verification for uncertain ones.",
  5: "Refresh queues anytime to pull the latest backend state.",
};

function fallbackLocationFromChargerId(chargerId: string): { lat: number; lon: number } {
  let hash = 0;
  for (let index = 0; index < chargerId.length; index += 1) {
    hash = (hash * 31 + chargerId.charCodeAt(index)) >>> 0;
  }
  // Keep fallback points in an Austin-like bounding box for map rendering.
  const lat = 30.16 + ((hash % 1000) / 1000) * 0.24;
  const lon = -97.92 + ((((hash / 1000) | 0) % 1000) / 1000) * 0.34;
  return { lat, lon };
}

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
  const [caseStatus, setCaseStatus] = useState<CaseStatusMap>({});

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

    const knownCases = [...baselineCases, ...certaintyCases];
    for (const item of knownCases) {
      if (!map[item.charger_id]) {
        const fallback = fallbackLocationFromChargerId(item.charger_id);
        map[item.charger_id] = {
          charger_id: item.charger_id,
          lat: fallback.lat,
          lon: fallback.lon,
        };
      }
    }

    return map;
  }, [baselineCases, certaintyCases]);

  const workflowStage: WorkflowStage = useMemo(() => {
    if (baselineCases.length === 0) return 1;
    if (certaintyCases.length === 0) return 2;
    if (!selectedCase) return 3;
    if (!hasActionTaken) return 4;
    return 5;
  }, [baselineCases.length, certaintyCases.length, selectedCase, hasActionTaken]);

  useEffect(() => {
    void refreshMetrics();
    void hydrateCasesFromBackend();
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

  async function hydrateCasesFromBackend() {
    try {
      const [baselineData, certaintyData] = await Promise.all([getCases("baseline"), getCases("certainty")]);
      setBaselineCases(baselineData.cases);
      setCertaintyCases(certaintyData.cases);
      if (baselineData.cases.length > 0) {
        setSelection((prev) => prev ?? { mode: "baseline", caseId: baselineData.cases[0].id });
      } else if (certaintyData.cases.length > 0) {
        setSelection((prev) => prev ?? { mode: "certainty", caseId: certaintyData.cases[0].id });
      }
    } catch {
      // Keep empty state if backend has no persisted cases yet.
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
      const cases = (await getCases("baseline")).cases;
      setBaselineCases(cases);
      setHasActionTaken(false);
      selectFirstCaseIfNeeded("baseline", cases);
      setActionMessage(`Baseline queue loaded: ${cases.length} case(s).`);
      await refreshMetrics();
    } catch (error) {
      setActionError(error instanceof Error ? error.message : "Failed to load baseline queue");
    } finally {
      setLoading((prev) => ({ ...prev, baseline: false }));
    }
  }

  async function handleRunCertainty() {
    setLoading((prev) => ({ ...prev, certainty: true }));
    setActionError(null);
    setActionMessage(null);

    try {
      const cases = (await getCases("certainty")).cases;
      setCertaintyCases(cases);
      setVerificationTasks(
        cases
          .filter((item) => item.verification_required)
          .map((item) => ({
            id: `vt_${item.id}`,
            case_id: item.id,
            question: item.uncertainty_reasons?.[0] ?? "Low confidence requires verification.",
            owner: "OpsQA",
            status: "open" as const,
          })),
      );
      setHasActionTaken(false);
      selectFirstCaseIfNeeded("certainty", cases);
      const verificationCount = cases.filter((item) => item.verification_required).length;
      setActionMessage(`Certainty queue loaded: ${cases.length} case(s), ${verificationCount} verification task(s).`);
      await refreshMetrics();
    } catch (error) {
      setActionError(error instanceof Error ? error.message : "Failed to load certainty queue");
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
      setCaseStatus((prev) => ({
        ...prev,
        [selectedCase.id]: {
          ...prev[selectedCase.id],
          dispatched: true,
        },
      }));
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
      setCaseStatus((prev) => ({
        ...prev,
        [selectedCase.id]: {
          ...prev[selectedCase.id],
          verified: payload.result === "confirmed_issue",
          verificationResult: payload.result,
        },
      }));
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
          caseStatus={caseStatus}
          selectedCaseId={selection?.mode === "baseline" ? selection.caseId : null}
          isLoading={loading.baseline}
          onSelectCase={(mode, caseId) => setSelection({ mode, caseId })}
        />
        <CaseQueue
          title="Certainty Queue"
          mode="certainty"
          cases={certaintyCases}
          caseStatus={caseStatus}
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

      <CaseDetail
        selectedCase={selectedCase}
        selectedMode={selection?.mode ?? null}
        verificationTask={selectedTask}
        caseStatus={selectedCase ? caseStatus[selectedCase.id] : undefined}
      />
    </main>
  );
}
