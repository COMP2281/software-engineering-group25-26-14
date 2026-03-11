import { useState } from "react";

export default function TripDetailModal({ 
    trip, 
    onClose, 
    formatTime 
}) {
    if (!trip) return null;

    // state for collapsible sections
    const [showMetrics, setShowMetrics] = useState(true);
    const [showEfficiency, setShowEfficiency] = useState(true);
    const [showEvents, setShowEvents] = useState(true);
    const [showFeedback, setShowFeedback] = useState(true);

    // helper function to remove prefix from AI feedback
    const cleanFeedback = (text) => {
        return text.replace(/^Positive:\s*/i, "").replace(/^Negative:\s*/i, "");
    };

    // helper function to determine feedback colour
    const feedbackColour = (text) => {
        if (text.toLowerCase().startsWith("negative")) {
        return "text-red-600 dark:text-red-400";
        }
        if (text.toLowerCase().startsWith("positive")) {
        return "text-green-600 dark:text-green-400";
        }
        return "";
    };

    // helper function to format metric labels
    const formatMetricLabel = (key) => {
        return key
        .replace(/_/g, " ")
        .replace(/\brpm\b/i, "RPM")
        .replace(/\b\w/g, (c) => c.toUpperCase());
    };

    // helper function to format event names
    const formatEventName = (type) => {
        if (type === "high_rpm") return "High RPM";
        if (type === "hard_braking") return "Hard Braking";
        if (type === "harsh_throttle") return "Harsh Throttle";
        return type;
    };

    // helper function to determine score colour
    const getScoreColour = (score) => {
        if (score >= 80) return "bg-green-500";
        if (score >= 50) return "bg-yellow-500";
        return "bg-red-500";
    };

    // section header component for collapsible sections
    const SectionHeader = ({ title, open, toggle }) => (
        <div className="mb-4">
        <button
            onClick={toggle}
            className="w-full flex justify-between items-center text-left text-xl font-semibold hover:text-blue-500"
        >
            <span>{title}</span>
            <span className="text-sm">{open ? "▲" : "▼"}</span>
        </button>

        <div className="border-b border-slate-300 dark:border-slate-600 mt-2"></div>
        </div>
    );

    return (
        <div 
        className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
        onClick={onClose}
        >
        <div
            className="bg-white dark:bg-slate-800 rounded-lg shadow-lg w-full max-w-4xl overflow-y-auto max-h-[90vh] p-6 relative"
            onClick={(e) => e.stopPropagation()}
        >
            {/* Close button */}
            <button
            className="absolute top-4 right-4 text-slate-500 hover:text-slate-700 dark:hover:text-white text-xl font-bold"
            onClick={onClose}
            >
            ✕
            </button>

            <h2 className="text-2xl font-semibold mb-6">Trip Details</h2>

            {/* Basic Trip Info */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
            <div>
                <p><span className="font-medium">Start Time:</span> {formatTime(trip.start_time)}</p>
                <p><span className="font-medium">End Time:</span> {formatTime(trip.end_time)}</p>
                <p><span className="font-medium">Vehicle:</span> {trip.vehicle_make} {trip.vehicle_model}</p>
            </div>
            </div>

            {/* Trip Summary Widgets */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
            {/* Efficiency Score */}
            <div className="p-4 bg-slate-100 dark:bg-slate-700 rounded-lg text-center">
                <p className="text-sm text-slate-500 dark:text-slate-300 mb-1">Efficiency Score</p>
                <p className="text-xl font-semibold">{trip.efficiency_score}</p>
            </div>

            {/* Average Fuel Economy */}
            <div className="p-4 bg-slate-100 dark:bg-slate-700 rounded-lg text-center">
                <p className="text-sm text-slate-500 dark:text-slate-300 mb-1">Avg Fuel Economy</p>
                <p className="text-xl font-semibold">{trip.average_fuel_economy} L/100km</p>
            </div>

            {/* Event Count */}
            <div className="p-4 bg-slate-100 dark:bg-slate-700 rounded-lg text-center">
                <p className="text-sm text-slate-500 dark:text-slate-300 mb-1">Events</p>
                <p className="text-xl font-semibold">{trip.events ? trip.events.length : 0}</p>
            </div>
            </div>

            {/* Metrics & Thresholds */}
            <div className="mb-8">
            <SectionHeader
                title="Metrics"
                open={showMetrics}
                toggle={() => setShowMetrics(!showMetrics)}
            />

            {showMetrics && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">

                {/* Fuel & Efficiency */}
                <div className="p-4 rounded bg-slate-100 dark:bg-slate-700">
                    <p className="font-medium mb-2">Fuel & Efficiency</p>
                    <p>Total Fuel Used: {trip.total_fuel_used} L</p>
                    <p>Average Fuel Economy: {trip.average_fuel_economy} L/100km</p>
                </div>

                {/* Data Quality */}
                <div className="p-4 rounded bg-slate-100 dark:bg-slate-700">
                    <p className="font-medium mb-2">Data Quality</p>
                    <p>Confidence: {trip.confidence}</p>
                    <p>Missing Data: {trip.missing_data_percentage}%</p>
                    <p>Imputed Values: {trip.imputed_value_count}</p>
                </div>

                {/* Thresholds */}
                <div className="p-4 rounded bg-slate-100 dark:bg-slate-700">
                    <p className="font-medium mb-2">Thresholds</p>
                    <p>High RPM: {trip.thresholds.high_rpm}</p>
                    <p>Harsh Throttle: {trip.thresholds.harsh_throttle}</p>
                    <p>Hard Braking: {trip.thresholds.hard_braking}</p>
                </div>

                </div>
            )}
            </div>

            {/* Efficiency Score Section */}
            <div className="mb-8">
            <SectionHeader
                title="Efficiency Score"
                open={showEfficiency}
                toggle={() => setShowEfficiency(!showEfficiency)}
            />

            {showEfficiency && (
                <>
                {/* Overall Score */}
                <div className="mb-6">
                    <div className="flex justify-between mb-1 font-semibold">
                    <span>Overall Score</span>
                    <span>{trip.efficiency_score}</span>
                    </div>

                    <div className="w-full bg-slate-300 dark:bg-slate-600 rounded h-3">
                    <div
                        className={`${getScoreColour(trip.efficiency_score)} h-3 rounded`}
                        style={{ width: `${trip.efficiency_score}%` }}
                    />
                    </div>
                </div>

                {/* Score Breakdown */}
                <p className="font-medium mb-3 text-sm text-slate-600 dark:text-slate-300">
                    Breakdown
                </p>

                {Object.entries(trip.score_breakdown).map(([key, value]) => (
                    <div key={key} className="mb-3">
                    <div className="flex justify-between text-sm mb-1">
                        <span>{formatMetricLabel(key)}</span>
                        <span>{value}</span>
                    </div>

                    <div className="w-full bg-slate-300 dark:bg-slate-600 rounded h-2">
                        <div
                        className="bg-blue-500 h-2 rounded"
                        style={{ width: `${value}%` }}
                        />
                    </div>
                    </div>
                ))}
                </>
            )}
            </div>

            {/* Events */}
            <div className="mb-8">
            <SectionHeader
                title="Events"
                open={showEvents}
                toggle={() => setShowEvents(!showEvents)}
            />

            {showEvents && (
                <>
                {trip.events && trip.events.length > 0 ? (
                    <div className="space-y-2">
                    {trip.events.map((event, idx) => (
                        <div
                        key={idx}
                        className="p-3 rounded border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-700"
                        >
                        <p><span className="font-medium">Type:</span> {formatEventName(event.type)}</p>
                        <p><span className="font-medium">Timestamp:</span> {formatTime(event.timestamp)}</p>
                        <p><span className="font-medium">Duration:</span> {event.duration}s</p>

                        {event.context && (
                            <p>
                            <span className="font-medium">Context:</span> {event.context}
                            </p>
                        )}
                        </div>
                    ))}
                    </div>
                ) : (
                    <p className="text-slate-500">No events recorded for this trip.</p>
                )}
                </>
            )}
            </div>

            {/* AI Feedback */}
            <div>
            <SectionHeader
                title="AI Feedback"
                open={showFeedback}
                toggle={() => setShowFeedback(!showFeedback)}
            />

            {showFeedback && (
                <>
                {trip.ai_feedback && trip.ai_feedback.length > 0 ? (
                    <ul className="list-disc list-inside space-y-1">
                    {trip.ai_feedback.map((feedback, idx) => (
                        <li key={idx} className={feedbackColour(feedback)}>
                        {cleanFeedback(feedback)}
                        </li>
                    ))}
                    </ul>
                ) : (
                    <p className="text-slate-500">No AI feedback for this trip.</p>
                )}
                </>
            )}
            </div>

        </div>
        </div>
    );
}