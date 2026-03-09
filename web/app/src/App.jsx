import { useState, useEffect } from "react";

// import components 
import Navbar from "./components/Navbar";
import UploadWidget from "./components/UploadWidget";
import ScoreWidget from "./components/ScoreWidget";
import FuelEconomyWidget from "./components/FuelEconomyWidget";
import InefficientEventsWidget from "./components/InefficientEventsWidget";
import NewWidget from "./components/NewWidget";
import Sidebar from "./components/Sidebar";

// import API functions
import { uploadFiles, analyseTrips } from "./services/Api";

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

  const [fuelEconomy, setFuelEconomy] = useState(null); // average fuel economy across all trips

  // event counts across all trips
  const [eventCounts, setEventCounts] = useState({
    high_rpm: 0,
    hard_braking: 0,
    harsh_throttle: 0,
    total: null,
  });

  const [currentPage, setCurrentPage] = useState("dashboard"); // current page for sidebar navigation

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

      // update average score state
      updateAverageScore(tripData);

      // update fuel economy state
      updateFuelEconomy(tripData);

      // update event counts state
      updateEventCounts(tripData);

    } catch (error) {
      // handle network or unexpected errors
      setAnalysisMessage("Analysis failed: " + error.message);
    }
  };

  // compute and update average score based on trip data
  const updateAverageScore = (trips) => {
    const totalScore = trips.reduce(
      (acc, trip) => acc + trip.efficiency_score,
      0
    );
    const averageScore = Math.round(totalScore / trips.length);
    setScore(averageScore);
  };

  // compute and update average fuel economy based on trip data
  const updateFuelEconomy = (trips) => {
    const totalFuelEconomy = trips.reduce(
      (acc, trip) => acc + trip.average_fuel_economy,
      0
    );
    const avgFuelEconomy = totalFuelEconomy / trips.length;
    setFuelEconomy(avgFuelEconomy.toFixed(2));
  };

  // compute event counts across all trips and update eventCounts state
  const updateEventCounts = (trips) => {
    const counts = {
      high_rpm: 0,
      hard_braking: 0,
      harsh_throttle: 0,
    };
    
    trips.forEach((trip) => {
      trip.events?.forEach((event) => {
        if (event.type === "high_rpm") counts.high_rpm++;
        if (event.type === "hard_braking") counts.hard_braking++;
        if (event.type === "harsh_throttle") counts.harsh_throttle++;
      });
    });

    const total = counts.high_rpm + counts.hard_braking + counts.harsh_throttle;

    setEventCounts({
      ...counts,
      total,
    });
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
    <div className="min-h-screen flex bg-slate-100 dark:bg-slate-900 text-slate-900 dark:text-slate-100 transition-colors duration-300">
      {/* Sidebar */}
      <Sidebar 
        currentPage={currentPage} 
        setCurrentPage={setCurrentPage} 
      />

      {/* Main content */}
      <div className="flex-1 flex flex-col">
        <Navbar
          isDarkMode={isDarkMode}
          onToggleTheme={handleThemeToggle}
          currentPage={currentPage}
        />

        <main className="p-6 flex-1 overflow-auto">
          {currentPage === "dashboard" && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <UploadWidget
                files={files}
                uploadResults={uploadResults}
                uploadState={uploadState}
                allUploadsSuccessful={allUploadsSuccessful}
                analysisMessage={analysisMessage}
                disableUploadButton={disableUploadButton}
                onFileChange={handleFileChange}
                onUpload={handleUpload}
                className="h-auto md:h-[calc(100vh-120px)] md:min-h-[704px]"
              />

              <div className="flex flex-col gap-6">
                <ScoreWidget
                  score={score}
                  scoreLowThreshold={scoreLowThreshold}
                  scoreHighThreshold={scoreHighThreshold}
                  className="flex-1 md:min-h-[340px]"
                />
                <FuelEconomyWidget
                  fuelEconomy={fuelEconomy}
                  className="flex-1 md:min-h-[340px]"
                />
              </div>

              <div className="flex flex-col gap-6">
                <InefficientEventsWidget
                  totalEvents={eventCounts.total}
                  highRPM={eventCounts.high_rpm}
                  hardBraking={eventCounts.hard_braking}
                  harshThrottle={eventCounts.harsh_throttle}
                  className="flex-1 md:min-h-[340px]"
                />
                <NewWidget className="flex-1 md:min-h-[340px]" />
              </div>
            </div>
          )}

          {currentPage === "trips" && (
            <div className="flex flex-col">
              <p>This page will show trips</p>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}