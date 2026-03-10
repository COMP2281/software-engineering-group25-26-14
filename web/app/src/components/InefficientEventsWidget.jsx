import { useState } from "react";

export default function InefficientEventsWidget({
  totalEvents = null,
  highRPM = 0,
  hardBraking = 0,
  harshThrottle = 0,
  className
}) {
  const [hovered, setHovered] = useState(null);  // tracks which segment is hovered for tooltip

  // radius and circumference for the circle
  const radius = 16;
  const circumference = 2 * Math.PI * radius;

  // check if data has been uploaded and analysed
  const hasData = totalEvents !== null && totalEvents !== undefined;

  // compute segment percentages
  const highPct = hasData && totalEvents ? highRPM / totalEvents : 0;
  const brakePct = hasData && totalEvents ? hardBraking / totalEvents : 0;
  const throttlePct = hasData && totalEvents ? harshThrottle / totalEvents : 0;

  // segment lengths
  const highLength = highPct * circumference;
  const brakeLength = brakePct * circumference;
  const throttleLength = throttlePct * circumference;

  // segment offsets
  const brakeOffset = -highLength;
  const throttleOffset = -(highLength + brakeLength);

  // tooltip data
  const tooltipData = {
    high_rpm: { label: "High RPM", value: highRPM },
    hard_braking: { label: "Hard Braking", value: hardBraking },
    harsh_throttle: { label: "Harsh Throttle", value: harshThrottle },
  };

  return (
    <div className={`rounded border border-slate-300 bg-white p-6 shadow flex flex-col items-center dark:border-slate-700 dark:bg-slate-800 ${className}`}>
      
      <h2 className="text-lg font-semibold mb-4">
        Inefficient Driving Events
      </h2>

      <div className="flex-1 flex flex-col items-center justify-center w-full">

        {/* Circular chart */}
        <div className="relative w-40 h-40">

          <svg
            className="w-full h-full -rotate-90"
            viewBox="0 0 36 36"
          >

            {/* Background circle */}
            <circle
              cx="18"
              cy="18"
              r={radius}
              fill="none"
              className="stroke-slate-300 dark:stroke-slate-700"
              strokeWidth="2"
            />

            {/* High RPM segment */}
            <circle
              cx="18"
              cy="18"
              r={radius}
              fill="none"
              strokeWidth="2"
              strokeLinecap="butt"
              stroke={hovered === "high_rpm" && hasData ? "rgb(185 28 28)" : "rgb(239 68 68)"}
              strokeDasharray={`${highLength} ${circumference}`}
              onMouseEnter={() => hasData && setHovered("high_rpm")}
              onMouseLeave={() => setHovered(null)}
              className="transition-colors duration-200 cursor-pointer"
              pointerEvents={hasData ? "auto" : "none"}
            />

            {/* Hard Braking segment */}
            <circle
              cx="18"
              cy="18"
              r={radius}
              fill="none"
              strokeWidth="2"
              strokeLinecap="butt"
              stroke={hovered === "hard_braking" && hasData ? "rgb(202 138 4)" : "rgb(234 179 8)"}
              strokeDasharray={`${brakeLength} ${circumference}`}
              strokeDashoffset={brakeOffset}
              onMouseEnter={() => hasData && setHovered("hard_braking")}
              onMouseLeave={() => setHovered(null)}
              className="transition-colors duration-200 cursor-pointer"
              pointerEvents={hasData ? "auto" : "none"}
            />

            {/* Harsh Throttle segment */}
            <circle
              cx="18"
              cy="18"
              r={radius}
              fill="none"
              strokeWidth="2"
              strokeLinecap="butt"
              stroke={hovered === "harsh_throttle" && hasData ? "rgb(29 78 216)" : "rgb(59 130 246)"}
              strokeDasharray={`${throttleLength} ${circumference}`}
              strokeDashoffset={throttleOffset}
              onMouseEnter={() => hasData && setHovered("harsh_throttle")}
              onMouseLeave={() => setHovered(null)}
              className="transition-colors duration-200 cursor-pointer"
              pointerEvents={hasData ? "auto" : "none"}
            />

          </svg>

          {/* Show total events or tooltip */}
          <div className="absolute inset-0 flex items-center justify-center text-center pointer-events-none">
            {hovered && hasData ? (
              <div>
                <div className="text-sm text-slate-500">
                  {tooltipData[hovered].label}
                </div>
                <div className="text-2xl font-bold">
                  {tooltipData[hovered].value}
                </div>
              </div>
            ) : (
              <div>
                <div className="text-2xl font-bold">{hasData ? totalEvents : "--"}</div>
                <div className="text-xs text-slate-500">events</div>
              </div>
            )}
          </div>

        </div>

        {/* Legend */}
        <div className="mt-4 text-sm space-y-1">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 bg-red-500 rounded"></span>
            High RPM ({highRPM})
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 bg-yellow-400 rounded"></span>
            Hard Braking ({hardBraking})
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 bg-blue-500 rounded"></span>
            Harsh Throttle ({harshThrottle})
          </div>
        </div>

      </div>
    </div>
  );
}