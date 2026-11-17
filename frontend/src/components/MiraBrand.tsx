interface MiraBrandProps {
  compact?: boolean;
  inverted?: boolean;
}

export function MiraBrand({
  compact = false,
  inverted = false,
}: MiraBrandProps) {
  return (
    <div
      className={
        "mira-brand"
        + (compact ? " mira-brand--compact" : "")
        + (inverted ? " mira-brand--inverted" : "")
      }
      aria-label="MIRA"
    >
      <span
        className="mira-brand__mark"
        aria-hidden="true"
      >
        <svg
          viewBox="0 0 48 48"
          role="img"
          focusable="false"
        >
          <path
            d="M10 35V13L24 27L38 13V35"
            fill="none"
            stroke="currentColor"
            strokeWidth="4.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <circle
            cx="24"
            cy="36"
            r="3.2"
            className="mira-brand__dot"
          />
        </svg>
      </span>

      {!compact && (
        <span className="mira-brand__name">
          MIRA
        </span>
      )}
    </div>
  );
}
