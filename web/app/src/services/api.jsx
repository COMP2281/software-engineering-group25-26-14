// base API URL
const API_BASE_URL = "http://localhost:5000";

// upload files to backend
export async function uploadFiles(formData) {
  const response = await fetch(`${API_BASE_URL}/upload`, {
    method: "POST",
    body: formData,
  });

  return response.json();
}

// run trip analysis on uploaded data
export async function analyseTrips(formData) {
  const response = await fetch(`${API_BASE_URL}/analyse`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error("Analysis request failed");
  }

  return response.json();
}