export default function Navbar({ isDarkMode, onToggleTheme }) {
    return (
        <header className="border-b border-slate-300 bg-white p-4 flex items-center justify-between dark:border-slate-700 dark:bg-slate-800">
        <h1 className="font-bold text-xl">Dashboard</h1>

        {/* Theme toggle button */}
        <button
            type="button"
            onClick={onToggleTheme}
            className="rounded border border-slate-400 px-3 py-1 text-sm font-medium hover:bg-slate-200 dark:border-slate-500 dark:hover:bg-slate-700"
        >
            {isDarkMode ? "Switch to light" : "Switch to dark"}
        </button>
        </header>
    );
}