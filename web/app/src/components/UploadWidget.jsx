export default function UploadWidget({
    files,
    uploadResults,
    uploadState,
    allUploadsSuccessful,
    analysisMessage,
    disableUploadButton,
    onFileChange,
    onUpload,
    className
}) {
    return (
        <div className={`rounded border border-slate-300 bg-white p-6 shadow overflow-y-auto dark:border-slate-700 dark:bg-slate-800 ${className}`}>

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
            onChange={onFileChange}
            className="hidden"
            />
        </div>

        {!files.length && (
            <p className="text-xs text-slate-500 mb-4">
            Select at least one CSV file to enable upload
            </p>
        )}

        {/* Display selected files */}
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
            onClick={onUpload}
            disabled={disableUploadButton}
            className={`w-full rounded px-4 py-2 text-white font-medium transition-colors
            ${
            disableUploadButton
                ? "bg-slate-400 cursor-not-allowed"
                : "bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600 cursor-pointer"
            }`}
        >
            {uploadState === "uploading" ? "Uploading..." : "Upload"}
        </button>

        {/* Upload results and analysis status */}
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
                <p className="text-sm font-medium text-slate-700 dark:text-slate-300">
                    Sit tight, this may take a moment depending on the number and size of your files.
                </p>
                </div>
            )}

            {/* Analysis error message only */}
            {analysisMessage?.startsWith("Analysis failed:") && (
            <p className="text-sm text-red-600 dark:text-red-400 mt-2">
                {analysisMessage}
            </p>
            )}
            
            </div>
        )}
        </div>
  );
}