import type { Case, CaseMode } from "../lib/types";

type LocationPoint = {
  charger_id: string;
  lat: number;
  lon: number;
};

type CaseMapProps = {
  cases: Case[];
  selectedCaseId: string | null;
  locationIndex: Record<string, LocationPoint>;
  onSelectCase: (mode: CaseMode, caseId: string) => void;
};

type Pin = {
  id: string;
  chargerId: string;
  priority: number;
  confidence: number;
  verificationRequired: boolean;
  x: number;
  y: number;
};

function priorityClass(score: number): string {
  if (score >= 75) return "high";
  if (score >= 50) return "medium";
  return "low";
}

function normalizeCoordinates(points: LocationPoint[]): { minLat: number; maxLat: number; minLon: number; maxLon: number } {
  const lats = points.map((point) => point.lat);
  const lons = points.map((point) => point.lon);

  const dataMinLat = Math.min(...lats);
  const dataMaxLat = Math.max(...lats);
  const dataMinLon = Math.min(...lons);
  const dataMaxLon = Math.max(...lons);

  // Keep a wider viewport so small sample datasets do not pin to canvas corners.
  const centerLat = (dataMinLat + dataMaxLat) / 2;
  const centerLon = (dataMinLon + dataMaxLon) / 2;
  const latSpan = Math.max(dataMaxLat - dataMinLat, 0.18);
  const lonSpan = Math.max(dataMaxLon - dataMinLon, 0.24);

  return {
    minLat: centerLat - latSpan / 2,
    maxLat: centerLat + latSpan / 2,
    minLon: centerLon - lonSpan / 2,
    maxLon: centerLon + lonSpan / 2,
  };
}

function projectPin(
  lat: number,
  lon: number,
  bounds: { minLat: number; maxLat: number; minLon: number; maxLon: number },
): { x: number; y: number } {
  const lonSpan = Math.max(bounds.maxLon - bounds.minLon, 0.0001);
  const latSpan = Math.max(bounds.maxLat - bounds.minLat, 0.0001);

  const x = ((lon - bounds.minLon) / lonSpan) * 100;
  const y = 100 - ((lat - bounds.minLat) / latSpan) * 100;

  return { x: Math.min(Math.max(x, 4), 96), y: Math.min(Math.max(y, 6), 94) };
}

export function CaseMap({
  cases,
  selectedCaseId,
  locationIndex,
  onSelectCase,
}: CaseMapProps) {
  const points = Object.values(locationIndex);

  if (points.length === 0) {
    return (
      <section className="panel map-wrap">
        <div className="map-head">
          <h3>Case Map</h3>
        </div>
        <p className="muted">No location data available yet.</p>
      </section>
    );
  }

  const bounds = normalizeCoordinates(points);

  const pins: Pin[] = cases
    .map((entry) => {
      const location = locationIndex[entry.charger_id];
      if (!location) return null;
      const { x, y } = projectPin(location.lat, location.lon, bounds);
      return {
        id: entry.id,
        chargerId: entry.charger_id,
        priority: entry.priority_score,
        confidence: entry.confidence,
        verificationRequired: entry.verification_required,
        x,
        y,
      };
    })
    .filter((pin): pin is Pin => pin !== null);

  return (
    <section className="panel map-wrap">
      <div className="map-head">
        <h3>Case Map</h3>
        <p className="muted">Baseline queue view</p>
      </div>

      <p className="muted map-note">Click a pin to open that case in detail view.</p>

      <div className="map-canvas" role="region" aria-label="Case location map">
        {pins.map((pin) => {
          const isSelected = pin.id === selectedCaseId;
          return (
            <button
              key={pin.id}
              type="button"
              className={`map-pin ${priorityClass(pin.priority)} ${isSelected ? "selected" : ""}`}
              style={{ left: `${pin.x}%`, top: `${pin.y}%` }}
              onClick={() => onSelectCase("baseline", pin.id)}
              title={`${pin.id} | ${pin.chargerId} | priority ${pin.priority} | confidence ${(pin.confidence * 100).toFixed(0)}%`}
            >
              <span>{pin.priority}</span>
            </button>
          );
        })}
      </div>

      <div className="map-legend">
        <span className="badge high">High priority</span>
        <span className="badge medium">Medium priority</span>
        <span className="badge low">Lower priority</span>
        <span className="badge warn">Verification required</span>
      </div>
    </section>
  );
}
