import { useState } from "react";

export default function FuelEconomyWidget({ 
    fuelEconomy,
    className 
}) {
  const [unit, setUnit] = useState("L/100km");

  // convert between L/100km and mpg
  const toggleUnit = () => {
    setUnit((prev) => (prev === "L/100km" ? "mpg" : "L/100km"));
  };

  let displayValue =
    fuelEconomy !== null
        ? unit === "L/100km"
            ? Number(fuelEconomy).toFixed(2)
            : (282.481 / fuelEconomy).toFixed(1)
        : "--"; 

  return (
    <div className={`flex flex-col items-center justify-center rounded border border-slate-300 bg-white p-6 shadow dark:border-slate-700 dark:bg-slate-800 ${className}`}>
        <h2 className="text-lg font-semibold mb-4">Average Fuel Economy</h2>

        {/* Display fuel economy value and unit */}
        <div className="text-center mb-4 flex-1 flex flex-col justify-center">
            <span className="text-3xl font-bold text-blue-500">{displayValue}</span>
            <span className="block text-sm text-slate-500 dark:text-slate-400 mt-1">{unit}</span>
        </div>

        {/* Toggle unit button */}
        <button
            onClick={toggleUnit}
            className="rounded bg-blue-600 px-4 py-2 text-white font-medium hover:bg-blue-700 transition-colors dark:bg-blue-500 dark:hover:bg-blue-600 min-w-[160px]"
        >
            Show in {unit === "L/100km" ? "mpg" : "L/100km"}
        </button>
        </div>
  );
}