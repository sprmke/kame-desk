export function ListSummary({
  total,
  startIdx,
  endIdx,
  entityLabel,
  isLoading = false,
  isFetching = false,
}: {
  total: number;
  startIdx: number;
  endIdx: number;
  entityLabel: string;
  isLoading?: boolean;
  isFetching?: boolean;
}) {
  return (
    <p className="min-h-5 text-sm text-muted-foreground">
      {isLoading ? (
        <span className="inline-block h-3 w-28 animate-pulse rounded-full bg-muted" />
      ) : total === 0 ? (
        `No ${entityLabel}`
      ) : (
        <>
          <span className="font-semibold tabular-nums text-foreground">
            {startIdx.toLocaleString()}
          </span>
          <span className="mx-1 text-muted-foreground/50">-</span>
          <span className="font-semibold tabular-nums text-foreground">
            {endIdx.toLocaleString()}
          </span>
          <span className="mx-1.5">of</span>
          <span className="font-semibold tabular-nums text-foreground">
            {total.toLocaleString()}
          </span>
          <span className="ml-1.5">{entityLabel}</span>
          {isFetching && !isLoading ? (
            <span className="ml-2 text-muted-foreground/70">updating</span>
          ) : null}
        </>
      )}
    </p>
  );
}
