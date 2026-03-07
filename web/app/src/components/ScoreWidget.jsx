export default function ScoreWidget({ score, scoreLowThreshold, scoreHighThreshold }) {
  return (
    <div className="rounded border border-slate-300 bg-white p-6 shadow flex flex-col items-center justify-center dark:border-slate-700 dark:bg-slate-800">

      <h2 className="text-lg font-semibold mb-4">Average Efficiency Score</h2>

        {/* Gauge */}
        {/* modified from https://preline.co/docs/progress.html#gauge-progress */}
        <div className="flex flex-col items-center justify-center">

            <div className="relative w-40 h-40">
            <svg
                className="w-full h-full rotate-[135deg]"
                viewBox="0 0 36 36"
                xmlns="http://www.w3.org/2000/svg"
            >
                {/* Background arc */}
                <circle
                cx="18"
                cy="18"
                r="16"
                fill="none"
                className="stroke-current text-slate-300 dark:text-slate-700"
                strokeWidth="1.5"
                strokeDasharray="75 100"
                strokeLinecap="round"
                />

                {/* Score arc */}
                {/* Color based on score thresholds */}
                {score !== null && (
                <circle
                    cx="18"
                    cy="18"
                    r="16"
                    fill="none"
                    strokeWidth="1.5"
                    strokeDasharray={`${score * 0.75} 100`}
                    strokeLinecap="round"
                    className={`stroke-current ${
                    score < scoreLowThreshold
                        ? "text-red-500"
                        : score < scoreHighThreshold
                        ? "text-yellow-400"
                        : "text-green-500"
                    }`}
                />
                )}
            </svg>

            {/* Score text */}
            <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-center">
                {score === null ? (
                <span className="text-slate-400 text-sm">No score yet</span>
                ) : (
                <span
                    className={`text-3xl font-bold ${
                    score < scoreLowThreshold
                        ? "text-red-500"
                        : score < scoreHighThreshold
                        ? "text-yellow-400"
                        : "text-green-500"
                    }`}
                >
                    {score}
                </span>
                )}
            </div>
            </div>
        </div>
    </div>
  );
}