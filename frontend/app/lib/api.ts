import type {
  ApiResponse,
  BaselineTriageData,
  CaseMode,
  CasesData,
  CertaintyTriageData,
  CompareMetrics,
  DispatchData,
  DispatchRequest,
  Signal,
  VerifyData,
  VerifyRequest,
} from "./types";

async function parseEnvelope<T>(res: Response): Promise<T> {
  const payload = (await res.json()) as ApiResponse<T>;
  if (!payload.ok) {
    throw new Error(payload.error ?? "Request failed");
  }
  if (payload.data === null) {
    throw new Error("Missing response data");
  }
  return payload.data;
}

export async function runBaseline(signals: Signal[]): Promise<BaselineTriageData> {
  const res = await fetch("/api/triage/baseline", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ signals }),
  });
  return parseEnvelope<BaselineTriageData>(res);
}

export async function runCertainty(signals: Signal[]): Promise<CertaintyTriageData> {
  const res = await fetch("/api/triage/certainty", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ signals }),
  });
  return parseEnvelope<CertaintyTriageData>(res);
}

export async function getCases(mode: CaseMode): Promise<CasesData> {
  const res = await fetch(`/api/cases?mode=${mode}`);
  return parseEnvelope<CasesData>(res);
}

export async function dispatchCase(caseId: string, body: DispatchRequest): Promise<DispatchData> {
  const res = await fetch(`/api/cases/${caseId}/dispatch`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return parseEnvelope<DispatchData>(res);
}

export async function verifyCase(caseId: string, body: VerifyRequest): Promise<VerifyData> {
  const res = await fetch(`/api/cases/${caseId}/verify`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return parseEnvelope<VerifyData>(res);
}

export async function getCompareMetrics(): Promise<CompareMetrics> {
  const res = await fetch("/api/metrics/compare");
  return parseEnvelope<CompareMetrics>(res);
}
