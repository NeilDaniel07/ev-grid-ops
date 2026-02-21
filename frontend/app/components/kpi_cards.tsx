import type { CompareMetrics } from "../lib/types";

type KpiCardsProps = {
  metrics: CompareMetrics | null;
  isLoading: boolean;
  error: string | null;
};

function formatPercent(value: number | null): string {
  if (value === null || Number.isNaN(value)) {
    return "--";
  }
  return `${value.toFixed(1)}%`;
}

export function KpiCards({ metrics, isLoading, error }: KpiCardsProps) {
  const cards = [
    { label: "False Dispatch Reduction", value: formatPercent(metrics?.false_dispatch_reduction_pct ?? null) },
    { label: "Triage Time Reduction", value: formatPercent(metrics?.triage_time_reduction_pct ?? null) },
    { label: "Critical Catch Delta", value: formatPercent(metrics?.critical_catch_rate_delta_pct ?? null) },
  ];

  return (
    <section>
      <div className="kpi-grid">
        {cards.map((card) => (
          <article key={card.label} className="panel kpi-card">
            <p className="kpi-label">{card.label}</p>
            <p className="kpi-value">{isLoading ? "..." : card.value}</p>
          </article>
        ))}
      </div>
      {error ? <p className="alert error">{error}</p> : null}
    </section>
  );
}
