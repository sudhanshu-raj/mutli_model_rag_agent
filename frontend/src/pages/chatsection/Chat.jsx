import { useState, useEffect } from "react";
import styles from "./chat.module.css";
import UploadPopUp from "./UploadPopUp";
import { SVGIcon } from "../../component/fileIcons";
import workspaceAPI from "../../api_calls/workspaceManager";
import { truncateFileName } from "../../services/fileService"; // Import the truncateFileName function
import { processChatInput } from "../../api_calls/chatProcess"; // Import the processChatInput function
import ReactMarkdown from "react-markdown";
import MarkdownViewer from "../../utils/markdownViewer";
import { ENDPOINTS } from "../../api_calls/apiConfig"; // Import the UPLOAD_FILE_ACCESS constant

function ChatPage() {
  const [activeWorkspace, setActiveWorkspace] = useState(() => {
    const saved = localStorage.getItem("activeWorkspace");
    return saved ? JSON.parse(saved) : null;
  });

  // State to hold the files fetched from the active workspace
  const [workspaceFiles, setWorkspaceFiles] = useState([]);

  const [messages, setMessages] = useState([
    {
      id: 1,
      content: activeWorkspace
        ? `Hello! How can I assist you with your "${activeWorkspace.name}" workspace today?`
        : "Hello! How can I assist you today?",
      isAI: true,
    },
  ]);
  const [inputValue, setInputValue] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isUploadMenuOpen, setIsUploadMenuOpen] = useState(false);
  const [chatError, setChatError] = useState("");

  const [toogleState, setToggleState] = useState("text");

  const [deletingFileId, setDeletingFileId] = useState(null);

  const handleFileUploaded = (newFile) => {
    // Append the new file to the workspaceFiles array
    setWorkspaceFiles((prev) => [...prev, newFile]);
  };

  // Load files from API when activeWorkspace is set
  useEffect(() => {
    const loadWorkspaceFiles = async () => {
      if (activeWorkspace) {
        console.log("Fetching files for workspace:", activeWorkspace.name);
        const response = await workspaceAPI.getWorkspaceFiles(
          activeWorkspace.name
        );
        console.log("Workspace files response (Chat2.jsx):", response);
        if (response.success) {
          setWorkspaceFiles(response.data.data["files"] || []);
        } else {
          console.error("Error fetching workspace files:", response.error);
        }
      }
    };
    loadWorkspaceFiles();
  }, [activeWorkspace]);

  async function deleteWorkspaceFile(file) {
    const fileId = file.id || file.file_id;
    setDeletingFileId(fileId); // Set the ID of the file being deleted

    const workspaceInfo = {
      id: activeWorkspace.id,
      workspace_name: activeWorkspace.name,
    };
    const fileInfo = {
      id: fileId,
      file_name: file.file_name,
    };

    try {
      const response = await workspaceAPI.deleteWorkspaceFileDocID(
        workspaceInfo,
        fileInfo
      );
      if (response.success) {
        setWorkspaceFiles((prevFiles) =>
          prevFiles.filter((f) => {
            const id = f.id || f.file_id;
            return id !== fileId;
          })
        );
      } else {
        console.error("Error deleting file:", response.error);
      }
    } catch (error) {
      console.error("Error deleting file:", error);
    } finally {
      setDeletingFileId(null); // Clear the deletingFileId regardless of success/failure
    }
  }

  const processResponseLinks = (text) => {
    // Start with a very simple replacement to test if HTML rendering works
    console.log("Test text:", text); // Log the test text
    let imageCount = 0;
    return text.replace(/\[Image:?\s*([^\]]+)\]/gi, (match, url) => {
      imageCount++;
      return `<a href="${url.trim()}" target="_blank" rel="noopener noreferrer" class="image-link">📷 Image ${imageCount}</a>`;
    });
  };

  
  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;

    const newMessage = {
      id: messages.length + 1,
      content: inputValue,
      isAI: false,
    };

    setMessages([...messages, newMessage]);
    setInputValue("");
    setIsTyping(true);

    try {
      const response = await processChatInput(
        newMessage.content,
        toogleState,
        activeWorkspace.name
      );
      console.log("Raw response data:", JSON.stringify(response.data.answer)); 
      if (response.success === false) {
        console.error("Error processing chat input:", response.error);
        setChatError("Error processing chat input. Please try again.");
        setIsTyping(false);
        return;
      }
      const processedContent = processResponseLinks(response.data.answer);
      console.log("After processing:", processedContent);
      const aiResponse = {
        id: messages.length + 2,
        content: processedContent,
        isAI: true,
      };
      setMessages((prev) => [...prev, aiResponse]);
      setIsTyping(false);
    } catch (error) {
      console.error("Error processing chat input:", error);
      setIsTyping(false);
    }
  };

  // Optional helper function to detect file types by extension
  const getFileType = (fileName) => {
    const ext = fileName.split(".").pop().toLowerCase();
    if (ext === "pdf") return "pdf";
    if (["png", "jpg", "jpeg", "gif"].includes(ext)) return "image";
    if (ext === "txt") return "txt";
    return "txt"; // fallback icon
  };

  return (
    <div className={styles.app}>
      <aside
        className={`${styles.sidebar} ${isSidebarOpen ? styles.open : ""}`}
      >
        <div className={styles.sidebarHeader}>
          <h2>
            {activeWorkspace ? activeWorkspace.name : "Unknown Workspace"}
          </h2>
          <button
            className={styles.closeBtn}
            onClick={() => setIsSidebarOpen(false)}
          >
            ×
          </button>
        </div>

        <button
          className={styles.addSourceBtn}
          onClick={() => setIsUploadMenuOpen(true)}
        >
          + Add Source
        </button>

        {/* Render loaded files in the sidebar */}
        <div className={styles.filesList}>
          {workspaceFiles.map((file) => {
            const fileId = file.id || file.file_id;
            const isDeleting = deletingFileId === fileId;

            return (
              <div className={styles.fileItem} key={fileId}>
                <a
                  href={`${ENDPOINTS.UPLOAD_FILE_ACCESS}/${activeWorkspace.name}/${file.file_name}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={styles.fileLink}
                >
                  <span style={{ display: "flex", alignItems: "center" }}>
                    <SVGIcon
                      type={getFileType(file.file_name)}
                      style={{ marginRight: "6px" }}
                    />
                    {truncateFileName(file.file_name, 20)}
                  </span>
                </a>
                <button
                  className={styles.removeFile}
                  onClick={() => deleteWorkspaceFile(file)}
                  disabled={isDeleting}
                >
                  {isDeleting ? (
                    <div className={styles.smallLoader}></div>
                  ) : (
                    "×"
                  )}
                </button>
              </div>
            );
          })}
        </div>
      </aside>

      {isUploadMenuOpen && (
        <UploadPopUp
          onClose={() => setIsUploadMenuOpen(false)}
          onFileUploaded={handleFileUploaded}
        />
      )}

      <main className={styles.chatArea}>
        <header className={styles.mobileHeader}>
          <button
            className={styles.menuBtn}
            onClick={() => setIsSidebarOpen(true)}
          >
            ☰
          </button>
        </header>

        <div className={styles.messages}>
          {messages.map((message) => (
            <div
              key={message.id}
              className={`${styles.message} ${
                message.isAI ? styles.ai : styles.user
              }`}
            >
              {message.isAI ? (
                // <ReactMarkdown>{message.content}</ReactMarkdown>
                <MarkdownViewer markdownText={message.content} />
              ) : (
                message.content
              )}
            </div>
          ))}
          {isTyping && (
            <div className={`${styles.message} ${styles.ai} ${styles.typing}`}>
              <div className={styles.typingIndicator}>
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          )}
        </div>

        <div className={styles.inputArea}>
          <div className={styles.toggleWrapper}>
            <div className={styles.toogleContainer}>
              <div
                className={`${styles.slider} ${
                  toogleState === "text" ? styles.slideLeft : styles.slideRight
                }`}
              />
              <div
                className={styles.toogleOption}
                onClick={() => setToggleState("text")}
              >
                Text
              </div>
              <div
                className={styles.toogleOption}
                onClick={() => setToggleState("image")}
              >
                Image
              </div>
            </div>
          </div>

          <div className={styles.inputContainer}>
            <textarea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Type your message..."
              rows={3}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault(); // Prevent default behavior (newline)
                  if (inputValue.trim()) {
                    handleSendMessage();
                  }
                }
              }}
            />
            <button
              className={styles.sendBtn}
              onClick={handleSendMessage}
              disabled={!inputValue.trim()}
            >
              ➤
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}

export default ChatPage;
