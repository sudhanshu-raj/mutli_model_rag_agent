import { useState } from "react";
import { WaveAnimation } from "../../progressAnimation/WaveAnimation";
import { SVGIcon } from "../../../component/fileIcons";
import CheckIcon from "../../../assets/check.png";
import ErrorIcon from "../../../assets/close.png";
import Exclamation from "../../../assets/exclamation-mark.png";
import fileService from "../../../services/fileService";
import {
  processFile,
  getImageDescription,
  uploadFileFromLocal,
} from "../../../api_calls/fileUploadsRequest";
import workspaceAPI from "../../../api_calls/workspaceManager";

function LocalFileTab({ workspaceName, popStyle, onFileUploaded }) {
  // UI component states
  const [isUploadBtnClick, setIsUploadBtnClick] = useState(false);
  const [isImageFile, setIsImageFile] = useState(false);
  const [imageName, setImageName] = useState("");
  const [imageDescription, setImageDescription] = useState("");
  const [isFileAlreadyExists, setIsFileAlreadyExists] = useState(false);
  const [autoGenerate, setAutoGenerate] = useState(false);
  const [imageNameError, setImageNameError] = useState("");

  // Logic states
  const [isValidFile, setIsValidFile] = useState(false);
  const [isUploadDone, setIsUploadDone] = useState(false);
  const [isUploadSuccess, setIsUploadSuccess] = useState("");
  const [UploadResponse, setUploadResponse] = useState("");
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileInfo, setFileInfo] = useState(null);
  const [error, setError] = useState(null);
  const [fileUploadProgressToServer, setFileUploadProgressToServer] =
    useState(false);
  const [isFileUploadedToServer, setIsFileUploadedToServer] = useState(false);
  const [fileServerError, setFileServerError] = useState(null);

  const allowedExtensions = [
    "docx",
    "doc",
    "pdf",
    "txt",
    "json",
    "jpg",
    "png",
    "jpeg",
    "md",
    "webp",
  ];
  const MAX_FILE_SIZE_MB = 10;

  const handleUploadBtn = async (e) => {
    e.preventDefault();
    console.log("Upload Button Clicked");

    setIsValidFile(false);
    if (fileInfo && fileInfo.mime_type) {
      const file_type = fileInfo.mime_type.split("/")[0];
      if (file_type === "image") {
        setIsImageFile(true);
        return;
      }
    }
    setIsUploadBtnClick(true);
    const dataToSend = {
      file_path: fileInfo.name,
      workspace_name: workspaceName,
    };

    try {
      console.log("Data to be sent:", dataToSend);

      const processResponse = await processFile(dataToSend);
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
        console.log("File Upload Response for adding file in database:", response);
        if (response.success) {
          const newFileInfo = {
            file_id: response.data.data["file_id"],
            file_name: response.data.data["file_name"],
            workspace_name: response.data.data["workspace_name"],
          };
         
          //now add the doc_id to the file
          var created_doc_ids = processResponse.data.data["doc_id"];
          if (!Array.isArray(created_doc_ids)) {
            created_doc_ids = [created_doc_ids];
          }
          let docIDResponse = await workspaceAPI.addWorkspaceFileDocID(
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
          console.log("File uploaded to workspace table successfully.");
          }
          //here i adding file to sidemenu as we have to implmenent a proper reverse procees
          //till then it will be here so that i can  still recognize some  file has processed
          onFileUploaded(newFileInfo);
        } else {
          console.log(
            "Error adding file to workspace table workspace_files :",
            response.error
          );
          setUploadResponse("Error processing file");
          setIsUploadSuccess(false);
        }
      }
     
    } catch (error) {
      console.error("Error processing file:", error);
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
    setIsUploadBtnClick(true);
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
        console.log("File Upload Response of adding into table:", response);
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
      }
      
      setImageName("");
      setImageDescription("");
    } catch (error) {
      console.error("Unexpected Error processing image:", error);
      setUploadResponse("Unexpected rrror while processing file");
      setIsUploadSuccess(false);
    }
    setIsUploadDone(true);
  };

  const handleFileSelect = async (e) => {
    const file = e.target.files[0];
    console.log("selected file size", file.size);
    if (!file) return;

    setIsImageFile(false);
    setIsFileUploadedToServer(false);
    setFileServerError(null);
    setIsFileAlreadyExists(false);
    setSelectedFile(file);
    setIsUploadBtnClick(false);
    setIsUploadDone(false);
    const fileInfo = {
      name: file.name,
      size_human: formatFileSize(file.size),
      mime_type: file.type,
    };
    console.log("File Info:", fileInfo);
    setFileInfo(fileInfo);

    const fileExt = file.name.split(".").pop().toLowerCase();
    if (!allowedExtensions.includes(fileExt)) {
      setError(`File type not supported.`);
      return;
    }
    if (file.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
      setError(`File size exceeds ${MAX_FILE_SIZE_MB} MB.`);
      return;
    }

    setFileUploadProgressToServer(true);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("workspace_name", workspaceName);

    console.log("Data to be sent:", formData);

    const response = await uploadFileFromLocal(formData);
    console.log("File Upload Response:", response);
    setFileUploadProgressToServer(false);
    if (response.success === false) {
      const error = response.error.errors[0].error_type;
      setFileServerError(error); // Fixed: was calling the function instead of setting state
      setIsValidFile(false);
      return;
    }
    const fileData = response.data.data.uploaded_files[0];
    setIsFileUploadedToServer(true);
    if (fileData.already_exists) {
      setIsFileAlreadyExists(true);
      setFileServerError("File already exists in the workspace.");
      return;
    }
    //Reached here means file is uploaded successfully and not already exists
    setIsFileAlreadyExists(false);
    // Setting new fileinfo because something server side changes the file name
    const serverFileInfo = {
      name: fileData.filename,
      size_human: fileData.size_human,
      mime_type: fileData.mime_type,
    };
    setFileInfo(serverFileInfo);

    setIsValidFile(true);
    setError(null);
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + " B";
    else if (bytes < 1048576) return (bytes / 1024).toFixed(1) + " KB";
    else return (bytes / 1048576).toFixed(1) + " MB";
  };

  return (
    <div className={popStyle["upload-section"]}>
      <div className={popStyle["upload-icon"]}>⬆️</div>
      <p className={popStyle["upload-text"]}>
        Drag and drop or{" "}
        <label className={popStyle["choose-file"]}>
          choose file
          <input
            type="file"
            accept={allowedExtensions.map((ext) => `.${ext}`).join(",")}
            onChange={handleFileSelect}
            style={{ display: "none" }}
          />
        </label>{" "}
        to upload
      </p>
      <p className={popStyle["upload-subtext"]}>
        Supported file types: PDF, .txt, Markdown, Images, Audio (e.g. mp3)
      </p>

      {selectedFile && isImageFile && (
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

      {selectedFile && !isImageFile && (
        <>
          {fileUploadProgressToServer && (
            <div className={popStyle["uploaded-doc-progress"]}>
              <p>Uploading the file</p>
            </div>
          )}

          {error && (
            <div className={popStyle["uploaded-doc"]}>
              <div className={popStyle["uploaded-doc-info"]}>
                <span>
                  <SVGIcon type="pdf" style={{ marginRight: "6px" }} />
                  {fileService.truncateFileName(selectedFile.name)}
                </span>
                <span>{formatFileSize(selectedFile.size)}</span>
              </div>
              <img src={ErrorIcon} alt="error" />
              <span>{error}</span>
            </div>
          )}

          {isFileUploadedToServer && !fileServerError ? (
            <div className={popStyle["selected-file-info"]}>
              <div className={popStyle["uploaded-doc"]}>
                <div className={popStyle["uploaded-doc-info"]}>
                  <span>
                    <SVGIcon type="pdf" style={{ marginRight: "6px" }} />
                    {fileService.truncateFileName(selectedFile.name)}
                  </span>
                  <span>{formatFileSize(selectedFile.size)}</span>
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
            </div>
          ) : (isFileAlreadyExists && fileServerError) && (
            <div className={popStyle["uploaded-doc"]}>
              <div className={popStyle["uploaded-doc-info"]}>
                <span>
                  <SVGIcon type="pdf" style={{ marginRight: "6px" }} />
                  {fileService.truncateFileName(fileInfo.name)}
                </span>
                <span>{fileInfo.size_human}</span>
              </div>
              <img src={Exclamation} alt="exclamation" />
              <span>{fileServerError}</span>
            </div>
          )}
          
          {(!isFileAlreadyExists && fileServerError) && 
            (
              <div className={popStyle["uploaded-doc"]}>
                <div className={popStyle["uploaded-doc-info"]}>
                  <span>
                    <SVGIcon type="pdf" style={{ marginRight: "6px" }} />
                    {fileService.truncateFileName(selectedFile.name)}
                  </span>
                  <span>{formatFileSize(selectedFile.size)}</span>
                </div>
                <img src={ErrorIcon} alt="error" />
                <span>{fileServerError}</span>
              </div>
            )
          }
          
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

export default LocalFileTab;
