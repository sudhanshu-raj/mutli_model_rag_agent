//import api from "axios";
import api from "./axiosInterceptor"; // Import the axios instance with interceptors
import { ApiLogger } from "../utils/logger";
import { API_BASE_URL,ENDPOINTS } from "./apiConfig";

// API endpoints


/**
 * Common function to make API calls with logging
 * @param {string} endpoint - API endpoint to call
 * @param {object} data - Data to send in the request
 * @param {string} method - HTTP method (GET, POST, etc.)
 * @returns {Promise} - Response from the API
 */
async function makeApiCall(endpoint, data, method = "POST") {
  const url = `${API_BASE_URL}${endpoint}`;
  
  // Log the request and get start time
  const startTime = ApiLogger.logRequest(endpoint, method, data);
  
  try {
    let response;
    
    if (method.toUpperCase() === "GET") {
      // For GET requests, send data as query parameters
      response = await api.get(url, { 
        params: data,
        headers: {
          "Content-Type": "application/json",
        }
      });
    } else {
      // For POST and other methods, send data in request body
      response = await api({
        method: method,
        url: url,
        data: data
      });
    }

    // Log successful response
    ApiLogger.logResponse(endpoint, response.status, response.data, startTime);
    
    return {
      success: true,
      data: response.data
    };
  } catch (error) {
    // Log error response
    ApiLogger.logError(endpoint, error, startTime);
    
    return {
      success: false,
      error: error.response ? error.response.data : error.message
    };
  }
}

/**
 * Upload a file from a URL
 * @param {string} fileURL - URL of the file to upload
 * @returns {Promise} - Response from the API
 */
async function uploadFileFromUrl(data) {
  return makeApiCall(ENDPOINTS.FILE_DOWNLOAD, data, "POST");
}

/**
 * Process a file
 * @param {object} data - Data for file processing
 * @returns {Promise} - Response from the API
 */
async function processFile(data) {
  return makeApiCall(ENDPOINTS.FILE_PROCESS, data, "POST");
}

/**
 * Get an image description
 * @param {string} imagePath - Path to the image
 * @returns {Promise} - Response from the API
 */
async function getImageDescription(imagePath) {
  return makeApiCall(ENDPOINTS.IMAGE_DESCRIPTION_GENERATE, { image_path: imagePath }, "GET");
}

/**
 * Upload a local file
 * @param {FormData} data - FormData containing the file
 * @returns {Promise} - Response from the API
 */
async function uploadFileFromLocal(data) {
  return makeApiCall(ENDPOINTS.FILE_UPLOAD, data, "POST");
}

export {
  uploadFileFromUrl,
  processFile,
  getImageDescription,
  uploadFileFromLocal
};

