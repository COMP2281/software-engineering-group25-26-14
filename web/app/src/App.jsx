import { useState, useEffect } from "react";

export default function App() {
  const [isDarkMode, setIsDarkMode] = useState(() => {
    const savedTheme = localStorage.getItem("theme");
    if (savedTheme) return savedTheme === "dark";

    return window.matchMedia("(prefers-color-scheme: dark)").matches;
  });

  const [files, setFiles] = useState([]);
  const [uploadResults, setUploadResults] = useState([]);
  const [uploadWarning, setUploadWarning] = useState("");

  // Sync the document class whenever the theme changes
  useEffect(() => {
    document.documentElement.classList.toggle("dark", isDarkMode);
    localStorage.setItem("theme", isDarkMode ? "dark" : "light");
  }, [isDarkMode]);

  const handleFileChange = (event) => {
  setFiles(Array.from(event.target.files));
  setUploadResults([]); // clear previous results
  setUploadWarning(""); // clear any previous warning
  };

  const handleThemeToggle = () => {
    setIsDarkMode((prev) => !prev);
  };

  const handleUpload = async () => {
  if (!files.length) {
    setUploadWarning("Please select at least one file.");
    return;
  }

  setUploadWarning(""); // clear warning
  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));

  try {
    const response = await fetch("http://localhost:5000/upload", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();

    const results = data.files.map((file) => ({
      name: file?.name || "Unknown file",
      status: file?.error ? "Unsuccessful" : "Successful",
      error: file?.error || null,
    }));

    setUploadResults(results);
  } catch (error) {
    setUploadResults([
      { name: "Upload failed", status: "Unsuccessful", error: error.message },
    ]);
  }
  };

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900 transition-colors flex flex-col dark:bg-slate-900 dark:text-slate-100">
      {/* Navbar */}
      <header className="border-b border-slate-300 bg-white p-4 flex items-center justify-between dark:border-slate-700 dark:bg-slate-800">
        <h1 className="font-bold text-xl">Dashboard</h1>
        <button
          type="button"
          onClick={handleThemeToggle}
          className="rounded border border-slate-400 px-3 py-1 text-sm font-medium hover:bg-slate-200 dark:border-slate-500 dark:hover:bg-slate-700"
        >
          {isDarkMode ? "Switch to light" : "Switch to dark"}
        </button>
      </header>

      {/* Main Content */}
      <main className="flex-1 p-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Upload Widget */}
        <div className="rounded border border-slate-300 bg-white p-6 shadow dark:border-slate-700 dark:bg-slate-800">
          <h2 className="text-lg font-semibold mb-2">Upload Data</h2>

          <p className="text-sm text-slate-600 dark:text-slate-400 pb-2">
            Choose one or more KIT formatted CSV files to upload:
          </p>

          <div className="mt-2 mb-4">
            <label
              htmlFor="file-upload"
              className="cursor-pointer rounded bg-green-500 px-4 py-2 text-white font-medium hover:bg-green-600 dark:bg-green-500 dark:hover:bg-green-600 transition-colors"
            >
              Choose Files
            </label>
            <input
              id="file-upload"
              type="file"
              accept=".csv"
              multiple
              onChange={handleFileChange}
              className="hidden"
            />
          </div>

          {files.length > 0 && (
            <div className="mb-4">
              <p className="text-sm font-medium text-slate-800 dark:text-slate-200 mb-1">
                Selected files:
              </p>
              <ul className="list-disc list-inside text-sm text-slate-700 dark:text-slate-300">
                {files.map((file, idx) => (
                  <li key={idx}>{file.name}</li>
                ))}
              </ul>
            </div>
          )}

          <button
            onClick={handleUpload}
            className="cursor-pointer w-full rounded bg-blue-600 px-4 py-2 text-white font-medium hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600 transition-colors"
          >
            Upload
          </button>

          {uploadWarning && (
            <p className="text-sm text-red-600 dark:text-red-400 my-2">
              {uploadWarning}
            </p>
          )}

          {uploadResults.length > 0 && (
            <div className="mt-4">
              <p className="text-sm font-medium text-slate-800 dark:text-slate-200 mb-1">
                Upload status:
              </p>
              {uploadResults.map((msg, idx) => (
                <div key={idx} className="mb-2">
                  <p className="text-sm text-slate-700 dark:text-slate-300">
                    {msg.name}:{" "}
                    <span
                      className={`font-medium ${
                        msg.status === "Successful"
                          ? "text-green-600 dark:text-green-400"
                          : "text-red-600 dark:text-red-400"
                      }`}
                    >
                      {msg.status}
                    </span>
                  </p>

                  {msg.status === "Unsuccessful" && msg.error && (
                    <p className="text-sm text-red-600 dark:text-red-400 pl-4">
                      {msg.error}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}