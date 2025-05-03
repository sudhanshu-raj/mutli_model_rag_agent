import { useState, useEffect } from "react";
import { WaveAnimation } from "../../progressAnimation/WaveAnimation";
import { SVGIcon } from "../../../component/fileIcons";
import CheckIcon from "../../../assets/check.png";
import ErrorIcon from "../../../assets/close.png";
import Exclamation from "../../../assets/exclamation-mark.png";
import fileService from "../../../services/fileService";
import {
  processFile,
  uploadFileFromLocal,
} from "../../../api_calls/fileUploadsRequest";
import workspaceAPI from "../../../api_calls/workspaceManager";

function TextPasteTab({ workspaceName, popStyle, onFileUploaded }) {
  const [pastedText, setPastedText] = useState("");
  const [isUploadBtnClick, setIsUploadBtnClick] = useState(false);
  const [isUploadDone, setIsUploadDone] = useState(false);
  const [isUploadSuccess, setIsUploadSuccess] = useState(false);
  const [UploadResponse, setUploadResponse] = useState("");
  const [isValidText, setIsValidText] = useState(false);
  const [error, setError] = useState(null);
  const [fileUploadProgressToServer, setFileUploadProgressToServer] =
    useState(false);
  const [isFileUploadedToServer, setIsFileUploadedToServer] = useState(false);
  const [fileServerError, setFileServerError] = useState(null);
  const [charCount, setCharCount] = useState(0);
  const [fileInfo, setFileInfo] = useState(null);
  const [isFileAlreadyExists, setIsFileAlreadyExists] = useState(false);

  useEffect(() => {
    setCharCount(pastedText.length);
    setIsValidText(pastedText.trim().length > 0);

    setError(null);
    setFileInfo(null);
    setIsFileAlreadyExists(false);
    setFileServerError(null);
    setIsUploadDone(false);
    setIsUploadSuccess(false);
    setIsUploadBtnClick(false);
    setFileUploadProgressToServer(false);
  }, [pastedText]);

  const handleUploadBtn = async (e) => {
    e.preventDefault();
    console.log("Upload Button Clicked");

    if (!isValidText) {
      setError("Please enter text content");
      return;
    }

    setIsUploadBtnClick(true);
    setFileUploadProgressToServer(true);
    setError(null);

    try {
      // Generate a filename based on the first 20 words + timestamp
      const fileNameFromText = pastedText
        .trim()
        .substring(0, 20) // Take only first 15 characters
        .replace(/[^a-zA-Z0-9_]/g, ""); // Remove special chars

      // Format date as "Mar-31-2025-14-30-45"
      const now = new Date();
      const readableTimestamp = [
        now.toLocaleString("en-US", { month: "short" }),
        now.getDate(),
        now.getFullYear(),
        now.getHours(),
        now.getMinutes(),
      ].join("-");

      const fileName = `${fileNameFromText || "text"}_${readableTimestamp}.txt`;

      // Create a File object from the pasted text
      const fileBlob = new Blob([pastedText], { type: "text/plain" });
      const textFile = new File([fileBlob], fileName, { type: "text/plain" });

      // Create file info for display
      const textFileInfo = {
        name: fileName,
        size_human: formatFileSize(textFile.size),
        mime_type: "text/plain",
      };
      setFileInfo(textFileInfo);

      // Step 1: Upload file to server
      const formData = new FormData();
      formData.append("file", textFile);
      formData.append("workspace_name", workspaceName);

      console.log("Uploading text file to server:", textFileInfo);
      const uploadResponse = await uploadFileFromLocal(formData);
      setFileUploadProgressToServer(false);

      if (uploadResponse.success === false) {
        const errorMsg =
          uploadResponse.error.errors?.[0]?.error_type ||
          "Failed to upload text";
        setFileServerError(errorMsg);
        setIsUploadSuccess(false);
        setIsUploadDone(true);
        return;
      }

      // Check if file already exists
      const fileData = uploadResponse.data.data.uploaded_files[0];
      setIsFileUploadedToServer(true);

      if (fileData.already_exists) {
        setIsFileAlreadyExists(true);
        setFileServerError("File already exists in the workspace.");
        setIsUploadDone(true);
        return;
      }

      // Update file info with server response
      const serverFileInfo = {
        name: fileData.filename,
        size_human: fileData.size_human,
        mime_type: fileData.mime_type,
      };
      setFileInfo(serverFileInfo);

      // Step 2: Process the uploaded file
      const processData = {
        file_path: serverFileInfo.name,
        workspace_name: workspaceName,
      };

      console.log("Processing uploaded text file:", processData);
      const processResponse = await processFile(processData);

      if (processResponse.success === false) {
        setUploadResponse(
          processResponse.error.error_type || "Failed to process text"
        );
        setIsUploadSuccess(false);
      } else {
        setUploadResponse("Doc Uploaded Successfully 🎉");
        setIsUploadSuccess(true);

        //Now add the file name to database too
        const response = await workspaceAPI.uploadFilesToWorkspace(
          workspaceName,
          serverFileInfo.name
        );
        console.log("File Upload Response:", response);
        if (response.success) {
          const newFileInfo = {
            file_id: response.data.data["file_id"],
            file_name: response.data.data["file_name"],
            workspace_name: response.data.data["workspace_name"],
          };
          //now add the doc_id to the file
          let created_doc_ids = processResponse.data.data["doc_id"];
          if (!Array.isArray(created_doc_ids)) {
            created_doc_ids = [created_doc_ids];
          }
          console.log("doc_ids sending for post api", created_doc_ids);
          const docIDResponse = await workspaceAPI.addWorkspaceFileDocID(
            workspaceName,
            newFileInfo.file_id,
            created_doc_ids
          );
          if (!docIDResponse.success) {
            console.log(
              "Error adding doc_id to workspace_files_docid:",
              docIDResponse.error
            );
            setUploadResponse("Error processing file");
            setIsUploadSuccess(false);
          }
          else{
          //reached here means all is good
          console.log("File uploaded to workspace table successfully.");
          }
          //here i adding file to sidemenu as we have to implmenent a proper file reverse procees
          //till then it will be heere so that i can  still recognize some  file has processed
          onFileUploaded(newFileInfo);
        } else {
          console.log(
            "Error uploading file to workspace table:",
            response.error
          );
          setUploadResponse("Error processing file");
          setIsUploadSuccess(false);
        }

        //setPastedText(""); // Clear after successful upload
      }
    } catch (error) {
      console.error("Error:", error);
      setUploadResponse("An unexpected error occurred");
      setIsUploadSuccess(false);
    } finally {
      setIsUploadDone(true);
      setIsValidText(false);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + " B";
    else if (bytes < 1048576) return (bytes / 1024).toFixed(1) + " KB";
    else return (bytes / 1048576).toFixed(1) + " MB";
  };

  return (
    <div className={popStyle["upload-section"]}>
      <div className={popStyle["paste-section"]}>
        <div className={popStyle["paste-container"]}>
          <textarea
            className={popStyle["paste-textarea"]}
            placeholder="Paste or type your text here..."
            value={pastedText}
            onChange={(e) => setPastedText(e.target.value)}
            disabled={isUploadBtnClick && !isUploadDone}
          ></textarea>

          <div className={popStyle["textarea-footer"]}>
            <div className={popStyle["char-counter"]}>
              <span>{charCount}</span>
            </div>

            <div className={popStyle["paste-controls"]}>
              <button
                className={popStyle["clear-btn"]}
                onClick={() => setPastedText("")}
                disabled={!pastedText || (isUploadBtnClick && !isUploadDone)}
              >
                Clear
              </button>
            </div>
          </div>
        </div>

        {isUploadBtnClick && fileInfo && (
          <>
            {fileUploadProgressToServer && (
              <div className={popStyle["uploaded-doc-progress"]}>
                <p>Uploading the text</p>
              </div>
            )}

            {isFileAlreadyExists ? (
              <div className={popStyle["uploaded-doc"]}>
                <div className={popStyle["uploaded-doc-info"]}>
                  <span>
                    <SVGIcon type="txt" style={{ marginRight: "6px" }} />
                    {fileService.truncateFileName(fileInfo.name)}
                  </span>
                  <span>{fileInfo.size_human}</span>
                </div>
                <img src={Exclamation} alt="exclamation" />
                <span>{fileServerError}</span>
              </div>
            ) : fileServerError ? (
              <div className={popStyle["uploaded-doc"]}>
                <div className={popStyle["uploaded-doc-info"]}>
                  <span>
                    <SVGIcon type="txt" style={{ marginRight: "6px" }} />
                    {fileService.truncateFileName(fileInfo.name)}
                  </span>
                  <span>{fileInfo.size_human}</span>
                </div>
                <img src={ErrorIcon} alt="error" />
                <span>{fileServerError}</span>
              </div>
            ) : (
              <div className={popStyle["uploaded-doc"]}>
                <div className={popStyle["uploaded-doc-info"]}>
                  <span>
                    <SVGIcon type="txt" style={{ marginRight: "6px" }} />
                    {fileService.truncateFileName(fileInfo.name)}
                  </span>
                  <span>{fileInfo.size_human}</span>
                </div>
                {!isUploadDone ? (
                  <WaveAnimation
                    className={popStyle["wave-animation"]}
                    paused={isUploadDone}
                    isUploadSuccess={isUploadSuccess}
                  />
                ) : isUploadSuccess ? (
                  <img src={CheckIcon} alt="check" />
                ) : (
                  <img src={ErrorIcon} alt="error" />
                )}
                {isUploadDone && (
                  <p className={popStyle["upload-status"]}>{UploadResponse}</p>
                )}
              </div>
            )}
          </>
        )}

        {error && !isUploadBtnClick && (
          <div className={popStyle["paste-error"]}>
            <span>⚠️ {error}</span>
          </div>
        )}

        <div className={popStyle["upload-menu-button"]}>
          <button
            type="submit"
            disabled={!isValidText || (isUploadBtnClick && !isUploadDone)}
            onClick={handleUploadBtn}
          >
            Upload Source
          </button>
        </div>
      </div>
    </div>
  );
}

export default TextPasteTab;
