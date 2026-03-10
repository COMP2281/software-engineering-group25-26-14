import { useState } from "react";
import TripDetailModal from "./TripDetailModal";

export default function TripsTable({
  trips,
  sortColumn,
  setSortColumn,
  sortDirection,
  setSortDirection,
  startDate,
  setStartDate,
  endDate,
  setEndDate,
  selectedMake,
  setSelectedMake,
  selectedModel,
  setSelectedModel,
}) {
  // state for currently selected trip in the modal
  const [selectedTrip, setSelectedTrip] = useState(null);

  // helper function to format timestamps
  const formatTime = (timestamp) => {
    if (!timestamp) return "-";
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  // sorting handler
  const handleSort = (column) => {
    if (sortColumn === column) {
      setSortDirection((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortColumn(column);
      setSortDirection("asc");
    }
  };

  // get unique makes and models for filter dropdowns
  const makes = [...new Set(trips.map((t) => t.vehicle_make))].sort();

  const models = [
    ...new Set(
      trips
        .filter((t) => t.vehicle_make === selectedMake)
        .map((t) => t.vehicle_model)
    ),
  ].sort();

  // apply filters
  const filteredTrips = trips.filter((trip) => {
    const tripDate = new Date(trip.start_time);  // filter by start date

    // select trips with start time within the selected date range
    if (startDate && tripDate < new Date(startDate)) return false;
    if (endDate && tripDate > new Date(endDate)) return false;

    // filter by selected make and model
    if (selectedMake && trip.vehicle_make !== selectedMake) return false;
    if (selectedModel && trip.vehicle_model !== selectedModel) return false;

    return true;
  });

  // calculate averages for filtered trips
  const averages =
    filteredTrips.length > 0
      ? {
          fuelUsed:
            filteredTrips.reduce(
              (sum, t) => sum + Number(t.total_fuel_used || 0),
              0
            ) / filteredTrips.length,
          fuelEconomy:
            filteredTrips.reduce(
              (sum, t) => sum + Number(t.average_fuel_economy || 0),
              0
            ) / filteredTrips.length,
          efficiency:
            filteredTrips.reduce(
              (sum, t) => sum + Number(t.efficiency_score || 0),
              0
            ) / filteredTrips.length,
        }
      : null;

  // sort the filtered trips
  const sortedTrips = [...filteredTrips].sort((a, b) => {
    if (!sortColumn) return 0;

    let valA = a[sortColumn];
    let valB = b[sortColumn];

    if (sortColumn === "start_time" || sortColumn === "end_time") {
      valA = new Date(valA);
      valB = new Date(valB);
    }

    if (valA < valB) return sortDirection === "asc" ? -1 : 1;
    if (valA > valB) return sortDirection === "asc" ? 1 : -1;
    return 0;
  });

  // class for header cells
  const headerClass = (column) => `
    px-4 py-3 font-semibold cursor-pointer transition-colors relative group bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600
  `;

  // tooltip text based on current sort state
  const tooltipText = (column) => {
    if (sortColumn !== column) return "Sort (ascending)";
    return sortDirection === "asc" ? "Sort (descending)" : "Sort (ascending)";
  };

  // header cell component
  const HeaderCell = ({ column, label, hideClasses = "" }) => (
    <th
      onClick={() => handleSort(column)}
      className={`${headerClass(column)} ${hideClasses}`}
    >
      <div className="relative inline-block">
        {label}
        <span
          className={`absolute top-full mt-2 opacity-0 group-hover:opacity-100 pointer-events-none whitespace-nowrap text-xs px-2 py-1 rounded bg-slate-900 text-white dark:bg-slate-200 dark:text-black transition-opacity z-50 ${
            column === "efficiency_score"  // on small and medium screens, align tooltip to the right for the last column to prevent overflow
              ? "right-0 lg:left-0 lg:right-auto"
              : "left-0"
          }`}
        >
          {tooltipText(column)}
        </span>
      </div>
    </th>
  );

  // cell component
  const Cell = ({ children, hideClasses = "", className = "" }) => (
    <td className={`px-4 py-3 ${hideClasses} ${className}`}>{children}</td>
  );

  return (
    <div className="rounded border border-slate-300 bg-white shadow dark:border-slate-700 dark:bg-slate-800">
      <div className="p-6 border-b border-slate-200 dark:border-slate-700">
        {/* Filters */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 items-end">

          {/* Start Date */}
          <div>
            <label className="block text-sm font-medium mb-1">Start Date</label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full rounded border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-700"
            />
          </div>

          {/* End Date */}
          <div>
            <label className="block text-sm font-medium mb-1">End Date</label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-full rounded border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-700"
            />
          </div>

          {/* Vehicle Make */}
          <div>
            <label className="block text-sm font-medium mb-1">Vehicle Make</label>
            <select
              value={selectedMake}
              onChange={(e) => {
                setSelectedMake(e.target.value);
                setSelectedModel("");
              }}
              className="w-full rounded border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-700"
            >
              <option value="">All</option>
              {makes.map((make) => (
                <option key={make} value={make}>
                  {make}
                </option>
              ))}
            </select>
          </div>

          {/* Vehicle Model */}
          <div>
            <label className="block text-sm font-medium mb-1">Vehicle Model</label>
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              disabled={!selectedMake}
              className="w-full rounded border border-slate-300 px-3 py-2 text-sm disabled:opacity-50 dark:border-slate-600 dark:bg-slate-700"
            >
              <option value="">All</option>
              {models.map((model) => (
                <option key={model} value={model}>
                  {model}
                </option>
              ))}
            </select>
          </div>

          {/* Reset Button */}
          <div className="flex lg:justify-end">
            <button
              onClick={() => {
                setStartDate("2024-01-01");
                setEndDate(new Date().toISOString().split("T")[0]);
                setSelectedMake("");
                setSelectedModel("");
              }}
              className="rounded bg-blue-600 px-4 py-2 text-white font-medium hover:bg-blue-700 transition-colors dark:bg-blue-500 dark:hover:bg-blue-600 cursor-pointer"
            >
              Reset Filters
            </button>
          </div>
        </div>

        {/* Summary */}
        {trips.length > 0 && (
          <div className="mt-6 border-t border-slate-200 dark:border-slate-700 pt-4">
            {averages ? (
              <>
                <div className="text-sm font-medium mb-2">
                  Summary for filtered events:
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                  <div className="rounded bg-slate-100 dark:bg-slate-700 p-3">
                    <span className="font-medium">Average Fuel Used:</span>{" "}
                    {averages.fuelUsed.toFixed(2)} L
                  </div>
                  <div className="rounded bg-slate-100 dark:bg-slate-700 p-3">
                    <span className="font-medium">Average Fuel Economy:</span>{" "}
                    {averages.fuelEconomy.toFixed(2)}
                  </div>
                  <div className="rounded bg-slate-100 dark:bg-slate-700 p-3">
                    <span className="font-medium">Average Efficiency Score:</span>{" "}
                    {averages.efficiency.toFixed(2)}
                  </div>
                </div>
              </>
            ) : (
              <div className="text-sm text-slate-500">
                {trips.length > 0 ? "No trips match the current filters." : null}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Table */}
      {/* End Time column hidden on medium and small screen */}
      {/* Total Fuel Used column hidden on small screens */}
      <table className="w-full text-sm table-auto">

        {/* Table header */}
        <thead className="bg-slate-100 dark:bg-slate-700">
          <tr className="text-left">
            <HeaderCell column="start_time" label="Start Time" />
            <HeaderCell
              column="end_time"
              label="End Time"
              hideClasses="hidden lg:table-cell"
            />
            <HeaderCell column="vehicle_make" label="Make" />
            <HeaderCell column="vehicle_model" label="Model" />
            <HeaderCell
              column="total_fuel_used"
              label="Fuel Used (L)"
              hideClasses="hidden md:table-cell"
            />
            <HeaderCell column="average_fuel_economy" label="Fuel Economy" />
            <HeaderCell column="efficiency_score" label="Score" />
          </tr>
        </thead>

        {/* Table body */}
        <tbody>
          {sortedTrips.length === 0 && trips.length === 0 ? (
            <tr>
              <td colSpan="7" className="text-center py-8 text-slate-500">
                Head over to the Dashboard to upload your trips and see them here!
              </td>
            </tr>
          ) : (
            sortedTrips.map((trip) => (
              <tr
                key={trip.trip_id}
                className="border-t border-slate-200 dark:border-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors cursor-pointer"
                onClick={() => setSelectedTrip(trip)}
              >
                <Cell>{formatTime(trip.start_time)}</Cell>
                <Cell hideClasses="hidden lg:table-cell">
                  {formatTime(trip.end_time)}
                </Cell>
                <Cell>{trip.vehicle_make}</Cell>
                <Cell>{trip.vehicle_model}</Cell>
                <Cell hideClasses="hidden md:table-cell">
                  {trip.total_fuel_used}
                </Cell>
                <Cell>{trip.average_fuel_economy}</Cell>
                <Cell className="font-semibold">{trip.efficiency_score}</Cell>
              </tr>
            ))
          )}
        </tbody>
      </table>

      {/* Trip Detail Modal */}
      <TripDetailModal
        trip={selectedTrip}
        onClose={() => setSelectedTrip(null)}
        formatTime={formatTime}
      />

    </div>
  );
}