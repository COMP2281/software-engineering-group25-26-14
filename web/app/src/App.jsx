import { useState, useEffect } from "react";

export default function App() {
  // use localStorage to persist theme preference
  const [isDarkMode, setIsDarkMode] = useState(() => {
    const savedTheme = localStorage.getItem("theme");
    if (savedTheme) return savedTheme === "dark";
    return window.matchMedia("(prefers-color-scheme: dark)").matches;
  });
  
  // toggle theme
  const handleThemeToggle = () => {
    setIsDarkMode((prev) => !prev);
  };

  const [files, setFiles] = useState([]);  // array of selected File objects
  const [uploadResults, setUploadResults] = useState([]);  // array of { name, status, error } for each uploaded file

  const [uploadState, setUploadState] = useState("idle");  // status of the upload process
  // idle | uploading | analysing | done

  const [allUploadsSuccessful, setAllUploadsSuccessful] = useState(false);  // whether all uploads were successful

  const [analysisMessage, setAnalysisMessage] = useState("");  // message to show after analysis (success or error)

  // sync theme
  useEffect(() => {
    document.documentElement.classList.toggle("dark", isDarkMode);
    localStorage.setItem("theme", isDarkMode ? "dark" : "light");
  }, [isDarkMode]);

  // handle file selection
  const handleFileChange = (event) => {
    setFiles(Array.from(event.target.files));  // update files array
    setUploadResults([]);  // reset previous upload results
    setUploadState("idle");  // reset upload state
  };

  // upload files
  const handleUpload = async () => {
    setUploadState("uploading");  // set state to uploading

    // prepare form data to send files to backend
    const formData = new FormData();
    files.forEach((file) => formData.append("files", file));

    // wrap api call in try-catch to handle network errors
    try {
      // send files to backend
      const response = await fetch("http://localhost:5000/upload", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();  // wait for response and parse as JSON

      // create results array based on backend response
      const results = data.files.map((file) => ({
        name: file?.name || "Unknown file",  // file name 
        status: file?.error ? "Unsuccessful" : "Successful",  // status based on presence of error  
        error: file?.error || null,  // error message if any
      }));

      setUploadResults(results);  // update upload results state

      // check if all uploads were successful
      const allSuccessful = results.every((r) => r.status === "Successful");
      setAllUploadsSuccessful(allSuccessful);

      // if all uploads were successful, proceed to analysis step
      if (allSuccessful) {
        setUploadState("analysing");

        // call analysis endpoint
        try {
          const analyseResponse = await fetch("http://localhost:5000/analyse", {
            method: "POST",
            body: formData,
          });

          const analyseData = await analyseResponse.json();
          if (analyseData?.message) {
            setAnalysisMessage(`${analyseData.message}. The data from the analysis would be used for visualisations etc on other dashboard widgets TBA`);
          }
        } catch (error) {
          setAnalysisMessage("Analysis failed: " + error.message);
        }
      }
    } catch (error) {
      // handle network or unexpected errors
      setUploadResults([
        { name: "Upload failed", status: "Unsuccessful", error: error.message },
      ]);
    } finally {
    // always set done at the end
    setUploadState("done");
    }
  };

  // disable upload button if:
  // - no files selected
  // - currently uploading or analysing
  // - upload done and all uploads were successful
  const disableUploadButton =
    !files.length ||
    uploadState === "uploading" ||
    uploadState === "analysing" ||
    (uploadState === "done" && allUploadsSuccessful);

  // main render
  return (
    <div className="min-h-screen bg-slate-100 text-slate-900 transition-colors flex flex-col dark:bg-slate-900 dark:text-slate-100">
      
      {/* Navbar */}
      <header className="border-b border-slate-300 bg-white p-4 flex items-center justify-between dark:border-slate-700 dark:bg-slate-800">
        <h1 className="font-bold text-xl">Dashboard</h1>

        {/* Theme toggle button */}
        <button
          type="button"
          onClick={handleThemeToggle}
          className="rounded border border-slate-400 px-3 py-1 text-sm font-medium hover:bg-slate-200 dark:border-slate-500 dark:hover:bg-slate-700"
        >
          {isDarkMode ? "Switch to light" : "Switch to dark"}
        </button>
      </header>

      {/* Main */}
      <main className="flex-1 p-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">

        {/* Upload data section */}
        <div className="rounded border border-slate-300 bg-white p-6 shadow dark:border-slate-700 dark:bg-slate-800">

          <h2 className="text-lg font-semibold mb-2">Upload Data</h2>

          <p className="text-sm text-slate-600 dark:text-slate-400 pb-2">
            Choose one or more KIT formatted CSV files to upload:
          </p>

          {/* File picker */}
          <div className="mt-2 mb-4">
            <label
              htmlFor="file-upload"
              className="cursor-pointer rounded bg-green-500 px-4 py-2 text-white font-medium hover:bg-green-600 transition-colors"
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

          {/* Helper text when no files */}
          {!files.length && (
            <p className="text-xs text-slate-500 mb-4">
              Select at least one CSV file to enable upload
            </p>
          )}

          {/* Selected files */}
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

          {/* Upload button */}
          <button
            onClick={handleUpload}
            disabled={disableUploadButton}
            className={`w-full rounded px-4 py-2 text-white font-medium transition-colors
              ${
                disableUploadButton
                  ? "bg-slate-400 cursor-not-allowed"
                  : "bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600"
              }`}
          >
            {uploadState === "uploading" ? "Uploading..." : "Upload"}
          </button>

          {/* Upload results */}
          {uploadResults.length > 0 && (
            <div className="mt-4">

              <p className="text-sm font-medium text-slate-800 dark:text-slate-200 mb-1">
                Upload status:
              </p>

              {/* List each file's upload result with status and error message if unsuccessful */}
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

              {/* Overall status message based on whether all uploads were successful or not */}
              {allUploadsSuccessful && (
                <p className="text-sm text-green-600 dark:text-green-400 mt-2">
                  All files uploaded successfully.
                </p>
              )}

              {!allUploadsSuccessful && (
                <p className="text-sm text-red-600 dark:text-red-400 mt-2">
                  Some files have issues. Please ensure selected files are in the correct KIT CSV format and try again.
                </p>
              )}

              {/* Analysis spinner */}
              {uploadState === "analysing" && (
                <div className="mt-6 flex flex-col items-center gap-3">

                  <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>

                  <p className="text-sm font-medium text-slate-700 dark:text-slate-300">
                    Analysing your trips...
                  </p>

                </div>
              )}

              {/* Analysis complete message */}
              {analysisMessage && (
                <p className="text-sm text-blue-600 dark:text-blue-400 mt-2">
                  {analysisMessage}
                </p>
              )}

            </div>
          )}

        </div>

      </main>
    </div>
  );
}