import { useState } from "react";
import { WaveAnimation } from "../../progressAnimation/WaveAnimation";
import { SVGIcon } from "../../../component/fileIcons";
import CheckIcon from "../../../assets/check.png";
import ErrorIcon from "../../../assets/close.png";
import Exclamation from "../../../assets/exclamation-mark.png";
import fileService from "../../../services/fileService";
import {
  uploadFileFromUrl,
  processFile,
  getImageDescription,
} from "../../../api_calls/fileUploadsRequest";
import workspaceAPI from "../../../api_calls/workspaceManager";

function UrlFileTab({ workspaceName, popStyle, onFileUploaded }) {
  // UI component states
  const [isUploadBtnClick, setIsUploadBtnClick] = useState(false);
  const [isImageFile, setIsImageFile] = useState(false);
  const [imageName, setImageName] = useState("");
  const [imageDescription, setImageDescription] = useState("");
  const [isFileAlreadyExists, setIsFileAlreadyExists] = useState(false);
  const [autoGenerate, setAutoGenerate] = useState(false);
  const [imageNameError, setImageNameError] = useState("");

  // Logic states
  const [isEmptyURL, setIsEmptyURL] = useState(true);
  const [isValidFile, setIsValidFile] = useState(false);
  const [isUploadDone, setIsUploadDone] = useState(false);
  const [isUploadSuccess, setIsUploadSuccess] = useState(false);
  const [UploadResponse, setUploadResponse] = useState("");
  const [debounceTimer, setDebounceTimer] = useState(null);
  const [fileInfo, setFileInfo] = useState(null);
  const [error, setError] = useState(null);
  const [fileUploadProgress, setFileUploadProgress] = useState(false);

  const handleURLChange = (e) => {
    const url = e.target.value;
    setIsValidFile(false);
    setIsUploadBtnClick(false);
    setIsUploadDone(false);
    setUploadResponse("");
    setIsUploadSuccess(false);

    if (debounceTimer) {
      clearTimeout(debounceTimer);
    }
    if (!url) {
      setIsEmptyURL(true);
      setError(null);
      setFileInfo(null);
      setFileUploadProgress(false);
      return;
    }

    setIsEmptyURL(false);

    const timer = setTimeout(() => {
      setFileUploadProgress(true);
      setError(null);
      setFileInfo(null);

      // Process the URL after the delay
      handleExtractFileInfo(url);
    }, 800); // 800ms delay

    setDebounceTimer(timer);
  };

  const handleExtractFileInfo = async (fileUrl) => {
    if (!fileUrl) return;

    const dataToSend = {
      url: fileUrl,
      workspace_name: workspaceName,
    };
    const response = await uploadFileFromUrl(dataToSend);
    console.log("File Info Response:", response);
    setFileUploadProgress(false);

    if (
      response.success &&
      response.data.already_exists &&
      response.data.already_exists === true
    ) {
      setError("Seems file already there in the workspace.");
      setFileInfo(response.data.data);
      setIsFileAlreadyExists(true);
      return;
    }
    if (response.success === false) {
      console.error("Error:", response.error);
      if (response.error.error_type) {
        setError(response.error.error_type);
      } else {
        setError("Something went wrong, please try again later.");
      }
      setFileInfo(null);
      return;
    }
    //reached here means file is downloaded successfully
    setFileInfo(response.data.data);
    setIsValidFile(true);
    setError(null);
  };

  const handleUploadBtn = async (e) => {
    e.preventDefault();
    console.log("Upload Button Clicked");

    setIsUploadBtnClick(true);
    setIsValidFile(false);
    if (fileInfo && fileInfo.mime_type) {
      const file_type = fileInfo.mime_type.split("/")[0];
      if (file_type === "image") {
        setIsImageFile(true);
        return;
      }
    }

    try {
      const data = {
        file_path: fileInfo.name,
        workspace_name: workspaceName,
      };
      console.log("Data to be sent:", data);

      const processResponse = await processFile(data);
      console.log("File Process Response:", processResponse);

      if (processResponse.success === false) {
        setUploadResponse(processResponse.error.error_type);
        setIsUploadSuccess(false);
      } else {
        setIsUploadSuccess(true);
        setUploadResponse("Doc Uploaded Successfully 🎉");
        //Now add the file name to database too
        const response = await workspaceAPI.uploadFilesToWorkspace(
          workspaceName,
          fileInfo.name
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
          } else {
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
      }
    } catch (err) {
      console.log("Error in file processing:", err);
      setUploadResponse("Unexpected error while processing file");
      setIsUploadSuccess(false);
    }
    setIsUploadDone(true);
    
  };

  const handleImageSubmit = async () => {
    // Validate image name
    if (!imageName.trim()) {
      setImageNameError("Image name is required");
      return;
    }

    // Clear any previous errors
    setImageNameError("");
    setIsImageFile(false);
    let descriptionToUse = imageDescription;
    try {
      if (autoGenerate) {
        const image_path = workspaceName + "/" + fileInfo.name;
        const response = await getImageDescription(image_path);
        console.log("Image Description Response:", response);
        if (response.success === false) {
          setUploadResponse(
            "Processing failed, try putting the description manually"
          );
          setIsUploadSuccess(false);
          setIsUploadDone(true);
          setImageName("");
          setImageDescription("");
          return;
        }
        descriptionToUse = response.data.data;
        setImageDescription(descriptionToUse);
      }

      const image_metadata = {
        image_name: imageName,
        image_description: descriptionToUse,
      };

      const dataToSend = {
        file_path: fileInfo.name,
        workspace_name: workspaceName,
        image_metadata: image_metadata,
      };
      console.log("Data to be sent for image:", dataToSend);

      const processResponse = await processFile(dataToSend);
      console.log("Image Process Response:", processResponse);

      if (processResponse.success === false) {
        setUploadResponse(processResponse.error.error_type);
        setIsUploadSuccess(false);
      } else {
        setIsUploadSuccess(true);
        setUploadResponse("Doc Uploaded Successfully 🎉");
        //Now add the file name to database too
        const response = await workspaceAPI.uploadFilesToWorkspace(
          workspaceName,
          fileInfo.name
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
          } else {
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
      }
    } catch (err) {
      console.log("Error in image processing:", err);
      setUploadResponse("Unexpected error while processing file");
      setIsUploadSuccess(false);
    }
    setIsUploadDone(true);
    setImageName("");
    setImageDescription("");
  };

  return (
    <div className={popStyle["upload-section"]}>
      <div className={popStyle["upload-section-link"]}>
        <input
          className={popStyle["upload-section-website-input"]}
          placeholder="Enter the Source URL"
          onChange={(e) => handleURLChange(e)}
          disabled={isUploadBtnClick && !isUploadDone}
        ></input>
      </div>
      <p className={popStyle["upload-subtext"]}>
        Supported file types: PDF, .txt, Markdown, Images, Audio (e.g. mp3)
      </p>

      {!isEmptyURL && isImageFile && (
        <div className={popStyle["uploaded-doc-image-input"]}>
          <p className={popStyle["image-input-ask-title"]}>
            Additional Step for Enhanced Image Retrieval
          </p>

          <div className={popStyle["input-group"]}>
            <label
              className={popStyle["input-label"]}
              style={{ marginTop: "20px" }}
            >
              Image Name <span className={popStyle["required-field"]}>*</span>
            </label>
            <input
              type="text"
              className={`${popStyle["upload-section-img-input"]} ${
                imageNameError ? popStyle["input-error"] : ""
              }`}
              placeholder="Enter descriptive name"
              value={imageName}
              onChange={(e) => {
                setImageName(e.target.value);
                if (e.target.value.trim()) setImageNameError("");
              }}
            />
            {imageNameError && (
              <div className={popStyle["error-message"]}>{imageNameError}</div>
            )}
          </div>

          <div className={popStyle["input-group"]}>
            <label className={popStyle["input-label"]}>Image Description</label>
            <textarea
              className={popStyle["upload-section-img-textarea"]}
              placeholder="Enter details about this image"
              value={imageDescription}
              onChange={(e) => setImageDescription(e.target.value)}
              disabled={autoGenerate}
            ></textarea>

            <div className={popStyle["checkbox-container"]}>
              <input
                type="checkbox"
                id="auto-generate"
                checked={autoGenerate}
                onChange={(e) => {
                  setAutoGenerate(e.target.checked);
                  if (e.target.checked) setImageDescription("");
                }}
              />
              <label htmlFor="auto-generate">
                Auto-generate description using AI
              </label>
            </div>
          </div>

          <button
            className={popStyle["upload-section-img-input-btn"]}
            onClick={handleImageSubmit}
            disabled={
              !imageName.trim() || (!imageDescription.trim() && !autoGenerate)
            }
          >
            Done
          </button>
        </div>
      )}

      {!isEmptyURL && !isImageFile && (
        <>
          {fileUploadProgress && (
            <div className={popStyle["uploaded-doc-progress"]}>
              <p>Downloading the file</p>
            </div>
          )}

          {(fileInfo || error) && (
            <>
              {!error ? (
                <div className={popStyle["uploaded-doc"]}>
                  <div className={popStyle["uploaded-doc-info"]}>
                    <span>
                      <SVGIcon type="pdf" style={{ marginRight: "6px" }} />
                      {fileService.truncateFileName(fileInfo.name)}
                    </span>
                    <span>{fileInfo.size_human}</span>
                  </div>
                  {!isUploadBtnClick ? (
                    <img src={CheckIcon} alt="check" />
                  ) : (
                    <>
                      <WaveAnimation
                        className={popStyle["wave-animation"]}
                        paused={isUploadDone}
                        isUploadSuccess={isUploadSuccess}
                      />
                      {isUploadDone && (
                        <p className={popStyle["upload-status"]}>
                          {UploadResponse}
                        </p>
                      )}
                    </>
                  )}
                </div>
              ) : isFileAlreadyExists ? (
                <div className={popStyle["uploaded-doc"]}>
                  <div className={popStyle["uploaded-doc-info"]}>
                    <span>
                      <SVGIcon type="pdf" style={{ marginRight: "6px" }} />
                      {fileService.truncateFileName(fileInfo.name)}
                    </span>
                    <span>{fileInfo.size_human}</span>
                  </div>
                  <img src={Exclamation} alt="exclamation" />
                  <span>{error}</span>
                </div>
              ) : (
                <div className={popStyle["uploaded-doc"]}>
                  <img src={ErrorIcon} alt="error" />
                  <span>{error}</span>
                </div>
              )}
            </>
          )}
        </>
      )}

      <div className={popStyle["upload-menu-button"]}>
        <button
          type="submit"
          disabled={!isValidFile}
          onClick={(e) => handleUploadBtn(e)}
        >
          Upload Source
        </button>
      </div>
    </div>
  );
}

export default UrlFileTab;
