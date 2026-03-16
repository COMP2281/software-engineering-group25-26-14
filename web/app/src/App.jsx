import { useState, useEffect } from "react";

// import components 
import Navbar from "./components/Navbar";
import UploadWidget from "./components/UploadWidget";
import ScoreWidget from "./components/ScoreWidget";
import FuelEconomyWidget from "./components/FuelEconomyWidget";
import InefficientEventsWidget from "./components/InefficientEventsWidget";
import Sidebar from "./components/Sidebar";
import TripsTable from "./components/TripsTable";
import TripSummaryWidget from "./components/TripSummaryWidget";

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

  const [fuelEconomy, setFuelEconomy] = useState(null); // average fuel economy across all trips

  const [tripSummary, setTripSummary] = useState({
    totalTrips: null,
    vehicleCounts: {},
    bestTripScore: null,
    bestTripStartTime: null,
    worstTripScore: null,
    worstTripStartTime: null,
  });

  // states for sorting
  const [sortColumn, setSortColumn] = useState(null);
  const [sortDirection, setSortDirection] = useState("asc");

  // states for filtering
  const [startDate, setStartDate] = useState("1900-01-01");  // default start date of 1st Jan 1900
  const [endDate, setEndDate] = useState(() =>  // default end date of today
    new Date().toISOString().split("T")[0]
  );
  const [selectedMake, setSelectedMake] = useState("");
  const [selectedModel, setSelectedModel] = useState("");

  // event counts across all trips
  const [eventCounts, setEventCounts] = useState({
    high_rpm: 0,
    hard_braking: 0,
    harsh_throttle: 0,
    total: null,
  });

  const [currentPage, setCurrentPage] = useState("dashboard"); // current page for sidebar navigation

  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false); // state to control mobile sidebar visibility

  const [sessionId, setSessionId] = useState(null);  // session ID to track user session

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
        setSessionId(data.session_id);
        setUploadState("analysing");

        // call analysis endpoint
        await runAnalysis(data.session_id);
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
  const runAnalysis = async (sessionId) => {
    // wrap api call in try-catch to handle network errors
    try {
      // send files for analysis and wait for response
      const analysisData = await analyseTrips({ session_id: sessionId });

      // update trips state
      const tripData = analysisData.trips;
      setTrips(tripData);

      // update average score state
      updateAverageScore(tripData);

      // update fuel economy state
      updateFuelEconomy(tripData);

      // update event counts state
      updateEventCounts(tripData);

      // update trip summary state
      updateTripSummary(tripData);

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

  // compute summary metrics for the trip summary widget
  const updateTripSummary = (trips) => {
    if (!trips.length) {
      setTripSummary({
        totalTrips: 0,
        vehicleCounts: {},
        bestTripScore: null,
        bestTripStartTime: null,
        worstTripScore: null,
        worstTripStartTime: null,
      });
      return;
    }

    const vehicleCounts = trips.reduce((acc, trip) => {
      const key = `${trip.vehicle_make} ${trip.vehicle_model}`;
      acc[key] = (acc[key] || 0) + 1;
      return acc;
    }, {});

    const bestTrip = trips.reduce(
      (best, trip) => (trip.efficiency_score > best.efficiency_score ? trip : best),
      trips[0]
    );

    const worstTrip = trips.reduce(
      (worst, trip) => (trip.efficiency_score < worst.efficiency_score ? trip : worst),
      trips[0]
    );

    setTripSummary({
      totalTrips: trips.length,
      vehicleCounts,
      bestTripScore: bestTrip.efficiency_score,
      bestTripStartTime: bestTrip.start_time ?? null,
      worstTripScore: worstTrip.efficiency_score,
      worstTripStartTime: worstTrip.start_time ?? null,
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
        mobileOpen={mobileSidebarOpen} 
        setMobileOpen={setMobileSidebarOpen} 
      />

      {/* Main content */}
      <div className="flex-1 flex flex-col">
      <Navbar
        isDarkMode={isDarkMode}
        onToggleTheme={handleThemeToggle}
        setMobileOpen={setMobileSidebarOpen}
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

              <div className="flex flex-col md:flex-row md:col-span-2 lg:flex-col lg:col-span-1 gap-6">
                <InefficientEventsWidget
                  totalEvents={eventCounts.total}
                  highRPM={eventCounts.high_rpm}
                  hardBraking={eventCounts.hard_braking}
                  harshThrottle={eventCounts.harsh_throttle}
                  className="flex-1 md:min-h-[340px]"
                />
                <TripSummaryWidget
                  totalTrips={tripSummary.totalTrips}
                  vehicleCounts={tripSummary.vehicleCounts}
                  bestTripScore={tripSummary.bestTripScore}
                  bestTripStartTime={tripSummary.bestTripStartTime}
                  worstTripScore={tripSummary.worstTripScore}
                  worstTripStartTime={tripSummary.worstTripStartTime}
                  className="flex-1 md:min-h-[340px]"
                />
              </div>
            </div>
          )}

          {currentPage === "trips" && (
            <TripsTable
              trips={trips}
              sortColumn={sortColumn}
              setSortColumn={setSortColumn}
              sortDirection={sortDirection}
              setSortDirection={setSortDirection}
              startDate={startDate}
              setStartDate={setStartDate}
              endDate={endDate}
              setEndDate={setEndDate}
              selectedMake={selectedMake}
              setSelectedMake={setSelectedMake}
              selectedModel={selectedModel}
              setSelectedModel={setSelectedModel}
            />
          )}

        </main>
      </div>
    </div>
  );
}