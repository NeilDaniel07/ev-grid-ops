import type { Case, CaseMode } from "../lib/types";

type CaseQueueProps = {
  title: string;
  mode: CaseMode;
  cases: Case[];
  selectedCaseId: string | null;
  isLoading: boolean;
  onSelectCase: (mode: CaseMode, caseId: string) => void;
};

function priorityClass(score: number): "high" | "medium" | "low" {
  if (score >= 75) return "high";
  if (score >= 50) return "medium";
  return "low";
}

export function CaseQueue({ title, mode, cases, selectedCaseId, isLoading, onSelectCase }: CaseQueueProps) {
  const sortedCases = [...cases].sort((a, b) => b.priority_score - a.priority_score);

  return (
    <section className="panel queue">
      <div className="queue-head">
        <h3>{title}</h3>
        <span className="muted">{isLoading ? "loading..." : `${sortedCases.length} cases`}</span>
      </div>

      {sortedCases.length === 0 ? (
        <p className="queue-empty">{isLoading ? "Running triage..." : "No cases yet. Run triage to populate this queue."}</p>
      ) : (
        <div className="case-list">
          {sortedCases.map((item) => {
            const isSelected = selectedCaseId === item.id;
            return (
              <button
                key={`${mode}-${item.id}`}
                onClick={() => onSelectCase(mode, item.id)}
                type="button"
                className={`case-row${isSelected ? " selected" : ""}`}
              >
                <p className="case-title">{item.id}</p>
                <p className="case-sub">Charger: {item.charger_id}</p>
                <div className="badges">
                  <span className={`badge ${priorityClass(item.priority_score)}`}>Priority {item.priority_score}</span>
                  <span className="badge">Confidence {(item.confidence * 100).toFixed(0)}%</span>
                  <span className="badge">{item.recommended_action}</span>
                  {item.verification_required ? <span className="badge warn">verification required</span> : null}
                </div>
              </button>
            );
          })}
        </div>
      )}
    </section>
  );
}
