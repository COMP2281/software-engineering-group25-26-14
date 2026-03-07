import { useState, useEffect } from "react";

// import components 
import Navbar from "./components/Navbar";
import UploadWidget from "./components/UploadWidget";
import ScoreWidget from "./components/ScoreWidget";

// import API functions
import { uploadFiles, analyseTrips } from "./services/api";

export default function App() {
  // dark mode state
  // use local storage to persist theme preference across sessions
  // if no preference saved, use system preference
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

  const [trips, setTrips] = useState([]);  // array of trip objects
  const [score, setScore] = useState(null);  // average score of all trips

  const scoreLowThreshold = 50;  // below this score, show red
  const scoreHighThreshold = 80;  // above this score, show green

  // sync theme
  useEffect(() => {
    document.documentElement.classList.toggle("dark", isDarkMode);
    localStorage.setItem("theme", isDarkMode ? "dark" : "light");
  }, [isDarkMode]);

  // handle file selection
  const handleFileChange = (event) => {
    setFiles(Array.from(event.target.files));  // update files array

    // reset states related to upload and analysis when new files are selected
    setUploadResults([]);
    setUploadState("idle");
    setAllUploadsSuccessful(false);
    setAnalysisMessage("");
  };

  // upload files
  const handleUpload = async () => {
    setUploadState("uploading");  // set state to uploading

    // prepare form data to send files to backend
    const formData = new FormData();
    files.forEach((file) => formData.append("files", file));

    // wrap api call in try-catch to handle network errors
    try {
      // send files to backend and wait for response
      const data = await uploadFiles(formData)

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
        await runAnalysis(formData);
      }

    } catch (error) {
      // handle network or unexpected errors
      setUploadResults([
        { name: "Upload failed", status: "Unsuccessful", error: error.message },
      ])
      setAllUploadsSuccessful(false);
    } finally {
      // always set done at the end
      setUploadState("done");
    }
  };

  // analayse files
  const runAnalysis = async (formData) => {
    // wrap api call in try-catch to handle network errors
    try {
      // send files for analysis and wait for response
      const analysisData = await analyseTrips(formData);

      if (analysisData?.message) {
        setAnalysisMessage(
          `${analysisData.message}. The data from the analysis would be used for visualisations etc on other dashboard widgets TBA`
        );
      }

      // update trips state
      const tripData = analysisData.trips;
      setTrips(tripData);

      // compute average score across all trips and update score state
      const totalScore = analysisData.trips.reduce(
        (acc, trip) => acc + trip.efficiency_score,
        0
      );
      const averageScore = Math.round(totalScore / analysisData.trips.length);
      setScore(averageScore);

    } catch (error) {
      // handle network or unexpected errors
      setAnalysisMessage("Analysis failed: " + error.message);
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

      <Navbar
        isDarkMode={isDarkMode}
        onToggleTheme={handleThemeToggle}
      />

      <main className="p-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 items-start">

        <UploadWidget
          files={files}
          uploadResults={uploadResults}
          uploadState={uploadState}
          allUploadsSuccessful={allUploadsSuccessful}
          analysisMessage={analysisMessage}
          disableUploadButton={disableUploadButton}
          onFileChange={handleFileChange}
          onUpload={handleUpload}
        />

        <ScoreWidget
          score={score}
          scoreLowThreshold={scoreLowThreshold}
          scoreHighThreshold={scoreHighThreshold}
        />

      </main>
    </div>
  );
}