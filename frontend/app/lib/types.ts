export type ApiResponse<T> = {
  ok: boolean;
  data: T | null;
  error: string | null;
};

export type SignalSource = "charger_api" | "311" | "ugc";
export type SignalStatus = "down" | "degraded" | "online" | "unknown";

export type Signal = {
  id: string;
  source: SignalSource;
  timestamp: string;
  charger_id: string;
  lat: number;
  lon: number;
  status: SignalStatus;
  text: string;
};

export type GridStressLevel = "normal" | "elevated" | "high";
export type RecommendedAction =
  | "dispatch_field_tech"
  | "remote_reset"
  | "needs_verification";
export type RootCauseTag = "payment_terminal" | "connector" | "network" | "unknown";
export type CaseMode = "baseline" | "certainty";

export type Case = {
  id: string;
  charger_id: string;
  priority_score: number;
  sla_hours: number;
  root_cause_tag: RootCauseTag;
  confidence: number;
  recommended_action: RecommendedAction;
  evidence_ids: string[];
  grid_stress_level: GridStressLevel;
  explanation: string;
  uncertainty_reasons: string[];
  verification_required: boolean;
};

export type VerificationTask = {
  id: string;
  case_id: string;
  question: string;
  owner: string;
  status: "open" | "done";
  result?: "confirmed_issue" | "false_alarm" | "needs_more_data";
};

export type WorkOrder = {
  id: string;
  case_id: string;
  assigned_team: string;
  due_at: string;
  state: "created" | "in_progress" | "done";
};

export type CompareMetrics = {
  false_dispatch_reduction_pct: number;
  triage_time_reduction_pct: number;
  critical_catch_rate_delta_pct: number;
};

export type TriageRequest = {
  signals: Signal[];
};

export type BaselineTriageData = {
  cases: Case[];
};

export type CertaintyTriageData = {
  cases: Case[];
  verification_tasks: VerificationTask[];
};

export type CasesData = {
  mode: CaseMode;
  cases: Case[];
};

export type DispatchRequest = {
  assigned_team: string;
  due_at: string;
  state: "created" | "in_progress" | "done";
};

export type DispatchData = {
  work_order: WorkOrder;
};

export type VerifyRequest = {
  result: "confirmed_issue" | "false_alarm" | "needs_more_data";
  notes?: string;
};

export type VerifyData = {
  verification_task: VerificationTask;
};
