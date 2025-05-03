//import api from "axios";
import api from "./axiosInterceptor"; // Import the axios instance with interceptors
import { ApiLogger } from "../utils/logger";
import { API_BASE_URL, ENDPOINTS } from "./apiConfig";

const processChatInput = async (inputData, questionType, workspace) => {
  const url = `${API_BASE_URL}${ENDPOINTS.CHATPROCESS}`;
  const startTime = ApiLogger.logRequest(ENDPOINTS.PROCESS_INPUT, "POST", { inputData, questionType, workspace });

  try {
    const response = await api.post(url, {
      inputData,
      questionType,
      workspace
    });

    ApiLogger.logResponse(ENDPOINTS.PROCESS_INPUT, response.status, response.data, startTime);

    return {
      success: true,
      data: response.data,
    };
  } catch (error) {
    ApiLogger.logError(ENDPOINTS.PROCESS_INPUT, error, startTime);

    return {
      success: false,
      error: error.response ? error.response.data : error.message,
    };
  }
}

export { processChatInput };
