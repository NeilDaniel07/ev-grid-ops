import type { Case, CaseMode, VerificationTask } from "../lib/types";

type CaseDetailProps = {
  selectedCase: Case | null;
  selectedMode: CaseMode | null;
  verificationTask: VerificationTask | null;
};

export function CaseDetail({ selectedCase, selectedMode, verificationTask }: CaseDetailProps) {
  if (!selectedCase || !selectedMode) {
    return (
      <section className="panel detail">
        <h3>Case Detail</h3>
        <p className="muted" style={{ marginTop: 8 }}>
          Select a case from either queue to view details.
        </p>
      </section>
    );
  }

  return (
    <section className="panel detail">
      <h3>Case Detail ({selectedMode})</h3>

      <div className="detail-grid">
        <div>
          <h4>Core Signals</h4>
          <div className="meta-grid">
            <p className="meta-item">
              <span>Case</span>
              {selectedCase.id}
            </p>
            <p className="meta-item">
              <span>Charger</span>
              {selectedCase.charger_id}
            </p>
            <p className="meta-item">
              <span>Priority</span>
              {selectedCase.priority_score}
            </p>
            <p className="meta-item">
              <span>Confidence</span>
              {(selectedCase.confidence * 100).toFixed(0)}%
            </p>
            <p className="meta-item">
              <span>SLA</span>
              {selectedCase.sla_hours}h
            </p>
            <p className="meta-item">
              <span>Root Cause</span>
              {selectedCase.root_cause_tag}
            </p>
            <p className="meta-item">
              <span>Action</span>
              {selectedCase.recommended_action}
            </p>
            <p className="meta-item">
              <span>Grid Stress</span>
              {selectedCase.grid_stress_level}
            </p>
          </div>
        </div>

        <div>
          <h4>Explainability</h4>
          <p>{selectedCase.explanation}</p>

          <h4 style={{ marginTop: 12 }}>Uncertainty Reasons</h4>
          {selectedCase.uncertainty_reasons.length === 0 ? (
            <p className="muted">None</p>
          ) : (
            <ul>
              {selectedCase.uncertainty_reasons.map((reason) => (
                <li key={reason}>{reason}</li>
              ))}
            </ul>
          )}

          <h4 style={{ marginTop: 12 }}>Evidence IDs</h4>
          <p>{selectedCase.evidence_ids.join(", ") || "None"}</p>

          <h4 style={{ marginTop: 12 }}>Verification</h4>
          {verificationTask ? (
            <div className="meta-grid">
              <p className="meta-item">
                <span>Task</span>
                {verificationTask.question}
              </p>
              <p className="meta-item">
                <span>Owner</span>
                {verificationTask.owner}
              </p>
              <p className="meta-item">
                <span>Status</span>
                {verificationTask.status}
              </p>
              <p className="meta-item">
                <span>Result</span>
                {verificationTask.result ?? "pending"}
              </p>
            </div>
          ) : (
            <p className="muted">
              {selectedCase.verification_required ? "Verification required but no task returned yet." : "Not required"}
            </p>
          )}
        </div>
      </div>
    </section>
  );
}
