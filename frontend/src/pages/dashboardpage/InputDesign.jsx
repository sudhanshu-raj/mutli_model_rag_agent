"use client";
import * as React from "react";
import { useState } from "react";
import styles from "./InputDesign.module.css";
import * as workspaceAPI  from "../../api_calls/workspaceManager";
import { useNavigate } from "react-router-dom";
import { useEffect } from "react";
import { useAuth } from "../../services/AuthContext";


const DeleteConfirmationModal = ({ 
  workspaceName, 
  onCancel, 
  onConfirm, 
  isLoading,
  deleteSuccess,
  deleteError 
}) => {
  // Auto-dismiss modal on success after 2 seconds
  React.useEffect(() => {
    let timer;
    if (deleteSuccess) {
      timer = setTimeout(() => {
        onCancel();
      }, 2000);
    }
    return () => clearTimeout(timer);
  }, [deleteSuccess, onCancel]);

  return (
    <div className={styles.dltmdlModalOverlay} onClick={isLoading || deleteSuccess ? null : onCancel}>
      <div className={styles.dltmdlModalContent} onClick={(e) => e.stopPropagation()}>
        {!isLoading && !deleteSuccess && !deleteError && (
          <>
            <h3>Confirm Delete</h3>
            <p>Are you sure you want to delete workspace "{workspaceName}"?</p>
            <div className={styles.dltmdlButtons}>
              <button 
                onClick={onCancel} 
                className={styles.dltmdlCancelBtn}
                disabled={isLoading}
              >
                Cancel
              </button>
              <button 
                onClick={onConfirm} 
                className={styles.dltmdlDeleteBtn}
                disabled={isLoading}
              >
                Delete
              </button>
            </div>
          </>
        )}

        {isLoading && (
          <div className={styles.dltmdlLoaderContainer}>
            <div className={styles.dltmdlLoader}></div>
            <p>Deleting workspace...</p>
          </div>
        )}

        {deleteSuccess && (
          <div className={styles.dltmdlSuccessContainer}>
            <div className={styles.dltmdlSuccessIcon}>
              <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#4CAF50" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                <polyline points="22 4 12 14.01 9 11.01"></polyline>
              </svg>
            </div>
            <h3>Workspace Deleted</h3>
            <p>"{workspaceName}" has been deleted successfully</p>
          </div>
        )}

        {deleteError && (
          <div className={styles.dltmdlErrorContainer}>
            <div className={styles.dltmdlErrorIcon}>
              <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#F44336" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="15" y1="9" x2="9" y2="15"></line>
                <line x1="9" y1="9" x2="15" y2="15"></line>
              </svg>
            </div>
            <h3>Error</h3>
            <p>Failed to delete "{workspaceName}"</p>
            <p className={styles.dltmdlErrorMessage}>{deleteError}</p>
            <div className={styles.dltmdlButtons}>
              <button onClick={onCancel} className={styles.dltmdlOkBtn}>OK</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// WorkspaceCard component for individual workspace items
const WorkspaceCard = ({ workspace,onDelete }) => {

  function handleDeleteClick(e,workspaceId) {
    e.preventDefault();
    e.stopPropagation();
    onDelete(workspace);

    // Logic to handle editing the workspace
    console.log(`Editing workspace with ID: ${workspaceId}`);
  }

  return (
    <article
      className={`${styles.div3} ${styles.builderB6873ae0f1c64c83bdcdea018569518d}`}
      tabIndex="0"
      aria-label={`Workspace: ${workspace.name}`}
    >
      <div className={styles.topDiv}>
      <h2 className={styles.h2}>{workspace.name}</h2>
      <button
      className={styles.deleteBtn} 
      onClick={(e)=>handleDeleteClick(e)}>
      x
      </button>
     
      </div>

      <div className={styles.div4}>
      <span className={styles.filesName}>
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-file-text">
    <path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"></path>
    <path d="M14 2v4a2 2 0 0 0 2 2h4"></path>
    <path d="M10 9H8"></path>
    <path d="M16 13H8"></path>
    <path d="M16 17H8"></path>
  </svg>
  <span style={{ paddingLeft: '10px', paddingRight:'5px'}}>{workspace.filesCount}</span>
  <span> files</span>
</span>
<span className={styles.filesName}>
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-clock">
    <circle cx="12" cy="12" r="10"></circle>
    <polyline points="12 6 12 12 16 14"></polyline>
  </svg>
  <span style={{ paddingLeft: '10px'}}>{workspace.lastModified}</span>
</span>
      </div>
    </article>
  );
};

// CreateWorkspaceModal component for the modal dialog
const CreateWorkspaceModal = ({
  workspaceName,
  setWorkspaceName,
  onCancel,
  onCreate,
  error,
}) => {
  // Handle ESC key to close modal
  React.useEffect(() => {
    const handleEscKey = (event) => {
      if (event.key === "Escape") {
        onCancel();
      }
    };

    document.addEventListener("keydown", handleEscKey);
    return () => {
      document.removeEventListener("keydown", handleEscKey);
    };
  }, [onCancel]);

  // Focus the input when modal opens
  const inputRef = React.useRef(null);
  React.useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, []);

  return (
    <div
      className={styles.div5}
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
    >
      <div className={styles.div6}>
        <h3 id="modal-title" className={styles.h3}>
          Create New Workspace
        </h3>
        <input
          ref={inputRef}
          className={`${styles.input} ${styles.builderD13254e4203a4026a254ffe35b2be588}`}
          type="text"
          placeholder="Enter workspace name"
          value={workspaceName}
          onChange={(event) => setWorkspaceName(event.target.value)}
          aria-label="Workspace name"
        />
        {error && <p className={styles.error}>{error}</p>}
        <div className={styles.div7}>
          <button
            className={`${styles.button2} ${styles.builderCc33823a53dd4289a8c09488abdd860f}`}
            onClick={onCancel}
          >
            Cancel
          </button>
          <button
            className={`${styles.button3} ${styles.builder3931c0753f574c25b6ccac86dbf5cd12}`}
            onClick={onCreate}
          >
            Create
          </button>
        </div>
      </div>
    </div>
  );
};

// Main InputDesign component
function DashboardPage() {
  const navigate = useNavigate();
  const {logout } = useAuth(); // Use AuthContext to get logout function
  
  // State variables
  const [showNewWorkspaceModal, setShowNewWorkspaceModal] = useState(false);
  const [workspaceName, setWorkspaceName] = useState("");
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(true); // New loading state
  const [fetchError, setFetchError] = useState(null); // New fetch error state
  const [workspaces, setWorkspaces] = useState([]);

  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [workspaceToDelete, setWorkspaceToDelete] = useState(null);
  
  const [isDeletingWorkspace, setIsDeletingWorkspace] = useState(false);
  const [deleteSuccess, setDeleteSuccess] = useState(false);
  const [deleteError, setDeleteError] = useState(null);
  
  // Fetch workspaces from API on component mount
  useEffect(() => {
    const fetchWorkspaces = async () => {
      setIsLoading(true);
      try {
        const response = await workspaceAPI.getAllWorkspaces();
        
        if (response.success) {
          console.log("Workspaces fetched successfully:", response.data);
          
          // Transform API response to match our workspace object structure
          const formattedWorkspaces = response.data.data.map(workspace => ({
            id: workspace.id,
            name: workspace.workspace_name,
            filesCount: workspace.total_files || 0,
            lastModified: workspace.last_modified.split(" ")[0]
          }));
          
          setWorkspaces(formattedWorkspaces);
          // Save to localStorage for offline access
          localStorage.setItem('workspaces', JSON.stringify(formattedWorkspaces));
        } else {
          console.error("Error fetching workspaces:", response.error);
          setFetchError("Failed to load workspaces. Using cached data if available.");
          
          // Fallback to localStorage if API fails
          const savedWorkspaces = localStorage.getItem('workspaces');
          if (savedWorkspaces) {
            setWorkspaces(JSON.parse(savedWorkspaces));
          }
        }
      } catch (error) {
        console.error("Exception while fetching workspaces:", error);
        setFetchError("Failed to load workspaces. Using cached data if available.");
        
        // Fallback to localStorage if API fails
        const savedWorkspaces = localStorage.getItem('workspaces');
        if (savedWorkspaces) {
          setWorkspaces(JSON.parse(savedWorkspaces));
        }
      } finally {
        setIsLoading(false);
      }
    };

    fetchWorkspaces();
  }, []); // Empty dependency array means this runs once on mount

  // Save workspaces to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem('workspaces', JSON.stringify(workspaces));
  }, [workspaces]);

  function toggleModal() {
    setShowNewWorkspaceModal(!showNewWorkspaceModal);
    setWorkspaceName("");
    setError(null); // Clear any previous errors
  }

  async function createWorkspace() {
    if (workspaceName.trim()) {
      setError(null);
      
      const response = await workspaceAPI.createWorkspace(workspaceName, "founder");
      console.log("Workspace created:", response);

      if (response.success === false) {
        setError("Error creating workspace");
        console.error("Error creating workspace at function:", response.error);
        return;
      }

      const data = response.data;
      if (data.already_exists) {
        setError("Workspace already exists");
        console.error("Error creating workspace at function:", "Workspace already exists");
        return;
      }

      const newWorkspace = {
        id: data.data.id,
        name: data.data.workspace_name,
        filesCount: 0,
        lastModified: data.data.last_modified.split(" ")[0]
      }
      
      console.log("New workspace created:", newWorkspace);
      const updatedWorkspaces = [...workspaces, newWorkspace];
      setWorkspaces(updatedWorkspaces);
      
      // Store the current active workspace
      localStorage.setItem('activeWorkspace', JSON.stringify(newWorkspace));
      
      // Close modal and reset input
      setWorkspaceName("");
      setShowNewWorkspaceModal(false);
      
      // Navigate to chat page with the new workspace
      navigate(`/chat`);
    }
  }

 // Called when user clicks delete on a workspace card
 const handleWorkspaceDelete = (workspace) => {
  setWorkspaceToDelete(workspace);
  setShowDeleteModal(true);
};

const confirmDeleteWorkspace = async () => {
  if (workspaceToDelete) {
    setIsDeletingWorkspace(true);
    setDeleteSuccess(false);
    setDeleteError(null);
    
    try {
      const deleteResponse = await workspaceAPI.deleteWorkspace(workspaceToDelete.name);
      console.log("Delete response:", deleteResponse);
      
      if (deleteResponse.success) {
        // Update workspaces in state
        const updatedWorkspaces = workspaces.filter(ws => ws.id !== workspaceToDelete.id);
        setWorkspaces(updatedWorkspaces);
        
        // Clear active workspace if it was deleted
        const active = localStorage.getItem("activeWorkspace");
        if (active && JSON.parse(active).id === workspaceToDelete.id) {
          localStorage.removeItem("activeWorkspace");
        }
        
        // Show success state
        setDeleteSuccess(true);
        setIsDeletingWorkspace(false);
        // Modal will auto-close after 2 seconds via useEffect in the modal
      } else {
        // Show error state
        setDeleteError(deleteResponse.error.message || "Unknown error occurred");
        setIsDeletingWorkspace(false);
      }
    } catch (error) {
      console.error("Exception while deleting workspace:", error);
      setDeleteError(error.message || "An unexpected error occurred");
      setIsDeletingWorkspace(false);
    }
  }
};

// Handle cancel delete
const cancelDeleteWorkspace = () => {
  setShowDeleteModal(false);
  setWorkspaceToDelete(null);
  setIsDeletingWorkspace(false);
  setDeleteSuccess(false);
  setDeleteError(null);
};

  // Function to handle workspace selection and navigation
  const handleWorkspaceSelect = (workspace) => {
    // Store selected workspace as active
    localStorage.setItem('activeWorkspace', JSON.stringify(workspace));
    // Navigate to chat page with the selected workspace
    navigate(`/chat`);
  }

  return (
    <main className={styles.div}>
      <header className={styles.header}>
        <h1 className={styles.h1}>My Workspaces</h1>
        <div className={styles.headerButtons}>
        <button
          className={`${styles.button} ${styles.builder406332cfa22246a8ad8c0f41622ad024}`}
          onClick={toggleModal}
          aria-label="Create new workspace"
        >
          <span style={{fontWeight:700}}>+ New Workspace</span>
        </button>

        <button 
        className={`${styles.logoutButton}`}
        onClick={logout}>
          Logout
        </button>
        </div>
      </header>

      <section className={styles.div2} aria-label="Workspaces list">
        {isLoading ? (
          <div className={styles.loadingContainer}>
            <p>Loading workspaces...</p>
            {/* You can add a spinner here */}
          </div>
        ) : fetchError ? (
          <div className={styles.errorContainer}>
            <p className={styles.errorMessage}>{fetchError}</p>
            {workspaces.length > 0 && (
              <p className={styles.usingCached}>Using cached workspaces.</p>
            )}
          </div>
        ) : workspaces.length === 0 ? (
          <div className={styles.emptyStateContainer}>
            <p>No workspaces found. Create your first workspace!</p>
          </div>
        ) : (
          workspaces.map((workspace) => (
            <div 
              key={workspace.id} 
              onClick={() => handleWorkspaceSelect(workspace)}
              className={styles.workspaceCardWrapper}
            >
              <WorkspaceCard workspace={workspace} 
              onDelete={() => (handleWorkspaceDelete(workspace))}/>
            </div>
          ))
        )}
      </section>

      {showNewWorkspaceModal && (
        <CreateWorkspaceModal
          workspaceName={workspaceName}
          setWorkspaceName={setWorkspaceName}
          onCancel={toggleModal}
          onCreate={createWorkspace}
          error={error}
        />
      )}

{showDeleteModal && workspaceToDelete && (
        <DeleteConfirmationModal
          workspaceName={workspaceToDelete.name}
          onCancel={cancelDeleteWorkspace}
          onConfirm={confirmDeleteWorkspace}
          isLoading={isDeletingWorkspace}
          deleteSuccess={deleteSuccess}
          deleteError={deleteError}
        />
      )}
    </main>
  );
}

export default DashboardPage;
