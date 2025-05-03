//workspaceApi.js - API functions
import axios from 'axios';
import api from './axiosInterceptor'; // Import the axios instance with interceptors
import { API_BASE_URL } from './apiConfig'; 

const API_URL = API_BASE_URL; 

const getSecretKey = () => {
  const userData = JSON.parse(localStorage.getItem('userData'));
  return userData?.value?.secret_key;
};

// Get all workspaces
export const getAllWorkspaces = async () => {
  try {
    const getSecretKeyVal = getSecretKey();
    const response = await api.get(`${API_URL}/workspaces/`);
    return {
      success: true,
      data: response.data
    };
  } catch (error) {
    console.error('Error fetching workspaces:', error);
    return {
      success: false,
      error: error.response ? error.response.data : error.message
    };
  }
};

// Get single workspace details
export const getWorkspaceDetails = async (workspaceName) => {
  try {
    const response = await api.get(`${API_URL}/workspaces/${workspaceName}`);
    return {
      success: true,
      data: response.data
    };
  } catch (error) {
    console.error(`Error fetching workspace ${workspaceName}:`, error);
    return {
      success: false,
      error: error.response ? error.response.data : error.message
    };
  }
};

// Create a new workspace
export const createWorkspace = async (workspaceName, userId = 'default_user') => {
  try {
    const response = await api.post(`${API_URL}/workspaces/`, {
      workspace_name: workspaceName,
      user_id: userId
    });
    return {
      success: true,
      data: response.data
    };
  } catch (error) {
    console.error('Error creating workspace:', error);
    return {
      success: false,
      error: error.response ? error.response.data : error.message
    };
  }
};

// Get files in a workspace
export const getWorkspaceFiles = async (workspaceName) => {
  try {
    const response = await api.get(`${API_URL}/workspaces/${workspaceName}/files`);
    return {
      success: true,
      data: response.data
    };
  } catch (error) {
    console.error(`Error fetching files for workspace ${workspaceName}:`, error);
    return {
      success: false,
      error: error.response ? error.response.data : error.message
    };
  }
};

// Upload files to a workspace
export const uploadFilesToWorkspace = async (workspaceName, fileName) => {
  try {
    const response = await api.post(
      `${API_URL}/workspaces/${workspaceName}/files`, 
      {
        file_name: fileName,
      }
    );
    return {
      success: true,
      data: response.data
    };
  } catch (error) {
    console.error(`Error uploading files to workspace ${workspaceName}:`, error);
    return {
      success: false,
      error: error.response ? error.response.data : error.message
    };
  }
};

// Delete a workspace
export const deleteWorkspace = async (workspaceName) => {
  try {
    const response = await api.delete(`${API_URL}/workspaces/${workspaceName}`);
    return {
      success: true,
      data: response.data
    };
  } catch (error) {
    console.error(`Error deleting workspace ${workspaceName}:`, error);
    return {
      success: false,
      error: error.response ? error.response.data : error.message
    };
  }
};



//get the doc_id of a file in a workspace
export const getWorkspaceFileDocID = async (workspaceName,fileId) => {
  try {
    const response = await api.get(`${API_URL}/workspaces/${workspaceName}/${fileId}/doc_ids`);
    return {
      success: true,
      data: response.data
    };
  } catch (error) {
    console.error(`Error fetching files for workspace ${workspaceName}:`, error);
    return {
      success: false,
      error: error.response ? error.response.data : error.message
    };
  }
};

// Upload doc_ids of a file in a workspace
export const addWorkspaceFileDocID= async (workspaceName, fileId,doc_ids) => {
  try {
    for(let i=0;i<doc_ids.length;i++){
         await api.post(
        `${API_URL}/workspaces/${workspaceName}/${fileId}/doc_ids`, 
        {
          doc_id: doc_ids[i],
        }
      );
    }
    return {
      success: true,
      data: "Doc_ids added successfully"
    };
  } catch (error) {
    console.error(`Error uploading files to workspace ${workspaceName}:`, error);
    return {
      success: false,
      error: error.response ? error.response.data : error.message
    };
  }
};

// Delete a file from a workspace
export const deleteWorkspaceFileDocID = async (workspaceInfo, fileInfo) => {
  try {
    const response = await api.delete(`${API_URL}/workspaces/delete/doc_ids`,{
      data:{
        workspaceInfo,
        fileInfo
      }
    });
    return {
      success: true,
      data: response.data
    };
  } catch (error) {
    console.error(`Error deleting file from workspace :`, error);
    return {
      success: false,
      error: error.response ? error.response.data : error.message
    };
  }
};


export default {
  getAllWorkspaces,
  getWorkspaceDetails,
  createWorkspace,
  getWorkspaceFiles,
  uploadFilesToWorkspace,
  deleteWorkspace,
  getWorkspaceFileDocID,
  addWorkspaceFileDocID,
  deleteWorkspaceFileDocID
};