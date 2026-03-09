import { useState } from "react";

// icons from FontAwesome
// https://fontawesome.com/icons
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faHouse, faCar } from "@fortawesome/free-solid-svg-icons";

export default function Sidebar({ currentPage, setCurrentPage }) {
  const [isOpen, setIsOpen] = useState(true);

  const linkClass = (page) =>
    `flex items-center gap-2 px-4 py-2 rounded cursor-pointer hover:bg-slate-200 dark:hover:bg-slate-700
    ${currentPage === page ? "bg-slate-300 dark:bg-slate-700" : ""}`;

  return (
    <aside
      className={`flex flex-col bg-white dark:bg-slate-800 border-r border-slate-300 dark:border-slate-700 transition-all duration-300 ${
        isOpen ? "w-48" : "w-16"
      }`}
    >
      {/* Collapse/Expand Button */}
      <button
        onClick={() => setIsOpen((prev) => !prev)}
        className="m-2 p-1 rounded bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 dark:hover:bg-slate-600 transition-colors"
      >
        {isOpen ? "«" : "»"}
      </button>

      <nav className="flex flex-col mt-4 gap-2">
        {/* Dashboard Link */}
        <div
          className={linkClass("dashboard")}
          onClick={() => setCurrentPage("dashboard")}
        >
          <div className="flex justify-center w-6">
            <FontAwesomeIcon icon={faHouse} />
          </div>
          <span
            className={`transition-all duration-300 overflow-hidden whitespace-nowrap ${
              isOpen ? "opacity-100 ml-2" : "opacity-0 w-0"
            }`}
          >
            Dashboard
          </span>
        </div>

        {/* Trips Link */}
        <div
          className={linkClass("trips")}
          onClick={() => setCurrentPage("trips")}
        >
          <div className="flex justify-center w-6">
            <FontAwesomeIcon icon={faCar} />
          </div>
          <span
            className={`transition-all duration-300 overflow-hidden whitespace-nowrap ${
              isOpen ? "opacity-100 ml-2" : "opacity-0 w-0"
            }`}
          >
            Trips
          </span>
        </div>
      </nav>
    </aside>
  );
}