const VITE_BACKEND_URL = import.meta.env.VITE_BACKEND_URL 
console.log("VITE_BACKEND_URL", VITE_BACKEND_URL)
export const API_BASE_URL = VITE_BACKEND_URL || "http://127.0.0.1:5000";

export const ENDPOINTS = {
    FILE_DOWNLOAD: "/files/download", 
    FILE_PROCESS: "/process_file/process",
    IMAGE_DESCRIPTION_GENERATE: "/process_file/generate_image_description",
    FILE_UPLOAD: "/files/upload",
    LOGS_UPLOAD: "/logs",
    CHATPROCESS: "/chat/process",
    UPLOAD_FILE_ACCESS: `${API_BASE_URL}/fileAccess/files`,
    AUTH_LOGIN: `${API_BASE_URL}/auth/validate`,
  };