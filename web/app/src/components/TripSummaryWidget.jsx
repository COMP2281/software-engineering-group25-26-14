export default function TripSummaryWidget({
  totalTrips = null,
  vehicleCounts = {},
  bestTripScore = null,
  bestTripStartTime = null,
  worstTripScore = null,
  worstTripStartTime = null,
  className,
}) {
  const hasData = totalTrips !== null && totalTrips > 0;

  const formatDate = (timestamp) => {
    if (!timestamp) return "-";
    return new Date(timestamp).toLocaleString(undefined, {
      dateStyle: "short",
      timeStyle: "short",
    });
  };

  return (
    <div className={`rounded border border-slate-300 bg-white p-6 shadow flex flex-col dark:border-slate-700 dark:bg-slate-800 ${className}`}>
      <h2 className="text-lg font-semibold mb-4 text-center">Trip Summary</h2>

      <div className="flex flex-col gap-4">
        {/* Total trips */}
        <div className="flex items-center justify-between">
          <span className="text-sm text-slate-500 dark:text-slate-400">Total Trips</span>
          <span className="text-lg font-bold">
            {hasData ? totalTrips : "--"}
          </span>
        </div>

        {/* Per vehicle breakdown */}
        {hasData ? (
          <div>
            <span className="text-sm text-slate-500 dark:text-slate-400 block mb-1">
              Trips per Vehicle
            </span>
            <div className="space-y-1">
              {Object.entries(vehicleCounts).map(([vehicle, count]) => (
                <div key={vehicle} className="flex items-center justify-between text-sm">
                  <span className="truncate text-slate-700 dark:text-slate-300">{vehicle}</span>
                  <span className="font-medium ml-2 shrink-0">{count}</span>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div>
            <span className="text-sm text-slate-500 dark:text-slate-400 block mb-1">
              Trips per Vehicle
            </span>
            <span className="text-sm text-slate-400">--</span>
          </div>
        )}

        {/* Best and worst trips */}
        <div className="grid grid-cols-2 gap-3">
          {/* Best trip */}
          <div className="rounded bg-green-50 dark:bg-green-900/20 p-3">
            <span className="text-xs font-semibold text-green-700 dark:text-green-400 block mb-1">
              Best Trip
            </span>
            {bestTripScore !== null ? (
              <>
                <span className="text-lg font-bold text-green-600 dark:text-green-400">
                  {bestTripScore}
                </span>
                <span className="text-xs text-slate-500 dark:text-slate-400 block mt-0.5">
                  {formatDate(bestTripStartTime)}
                </span>
              </>
            ) : (
              <span className="text-slate-400 text-sm">--</span>
            )}
          </div>

          {/* Worst trip */}
          <div className="rounded bg-red-50 dark:bg-red-900/20 p-3">
            <span className="text-xs font-semibold text-red-700 dark:text-red-400 block mb-1">
              Worst Trip
            </span>
            {worstTripScore !== null ? (
              <>
                <span className="text-lg font-bold text-red-600 dark:text-red-400">
                  {worstTripScore}
                </span>
                <span className="text-xs text-slate-500 dark:text-slate-400 block mt-0.5">
                  {formatDate(worstTripStartTime)}
                </span>
              </>
            ) : (
              <span className="text-slate-400 text-sm">--</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
