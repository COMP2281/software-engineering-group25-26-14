import { useState } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faHouse, faCar, faXmark } from "@fortawesome/free-solid-svg-icons";

export default function Sidebar({ 
    currentPage, 
    setCurrentPage, 
    mobileOpen, 
    setMobileOpen 
}) {
    const [isOpen, setIsOpen] = useState(true);

    const linkClass = (page) =>
        `flex items-center gap-2 px-4 py-2 rounded cursor-pointer hover:bg-slate-200 dark:hover:bg-slate-700
        ${currentPage === page ? "bg-slate-300 dark:bg-slate-700" : ""}`;

    return (
        <>
        {/* Desktop sidebar */}
        <aside
            className={`hidden md:flex flex-col bg-white dark:bg-slate-800 border-r border-slate-300 dark:border-slate-700 transition-all duration-300 ${
            isOpen ? "w-48" : "w-16"
            }`}
        >
            {/* Collapse/expand button */}
            <button
            onClick={() => setIsOpen((prev) => !prev)}
            className="m-2 p-1 rounded bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 dark:hover:bg-slate-600 transition-colors"
            >
            {isOpen ? "«" : "»"}
            </button>

            {/* Navigation links */}
            <nav className="flex flex-col mt-4 gap-2">
            <div className={linkClass("dashboard")} onClick={() => setCurrentPage("dashboard")}>
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
            <div className={linkClass("trips")} onClick={() => setCurrentPage("trips")}>
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

        {/* Mobile sidebar*/}
        {mobileOpen && (
            <>
            {/* Overlay */}
            <div className="fixed inset-0 z-40 flex md:hidden">
            <div
                className="fixed inset-0 bg-black opacity-25"
                onClick={() => setMobileOpen(false)}
            >
            </div>

            {/* Sidebar content */}
            <div className="relative flex flex-col bg-white dark:bg-slate-800 w-64 h-full border-r border-slate-300 dark:border-slate-700 transition-transform duration-300">
                {/* Close button */}
                <button
                onClick={() => setMobileOpen(false)}
                className="m-2 p-1 rounded bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 dark:hover:bg-slate-600"
                >
                <FontAwesomeIcon icon={faXmark} />
                </button>

                {/* Navigation links */}
                <nav className="flex flex-col mt-4 gap-2">
                <div className={linkClass("dashboard")} onClick={() => { setCurrentPage("dashboard"); setMobileOpen(false); }}>
                    <div className="flex justify-center w-6">
                    <FontAwesomeIcon icon={faHouse} />
                    </div>
                    <span className="ml-2">Dashboard</span>
                </div>
                <div className={linkClass("trips")} onClick={() => { setCurrentPage("trips"); setMobileOpen(false); }}>
                    <div className="flex justify-center w-6">
                    <FontAwesomeIcon icon={faCar} />
                    </div>
                    <span className="ml-2">Trips</span>
                </div>
                </nav>
            </div>
            </div>
            </>
        )}
        </>
    );
}