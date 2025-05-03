import { useState } from "react";
import popStyle from "./style.module.css";
import UrlFileTab from "./uploadPopUpTabs/urlFileTab";
import LocalFileTab from "./uploadPopUpTabs/localFileTab";
import TextPasteTab from "./uploadPopUpTabs/textPasteTab";

function UploadPopUp({ onClose,onFileUploaded }) {
  const [activeWorkspace, setActiveWorkspace] = useState(() => {
    const saved = localStorage.getItem("activeWorkspace");
    return saved ? JSON.parse(saved) : null;
  });

  // States for active tab selection
  const [websiteInput, setWebsiteInput] = useState(false);
  const [rawTextInput, setRawTextInput] = useState(false);
  const [localFileInput, setLocalFileInput] = useState(true);

  return (
    <div className={popStyle["upload-menu-overlay"]} onClick={onClose}>
      <div
        className={popStyle["upload-menu"]}
        onClick={(e) => e.stopPropagation()}
      >
        <div className={popStyle["upload-menu-header"]}>
          <h3 className={popStyle["upload-menu-title"]}>
            <span>Add sources</span>
          </h3>
          <button className={popStyle["upload-menu-close"]} onClick={onClose}>
            ×
          </button>
        </div>

        <div className={popStyle["upload-menu-content"]}>
          {localFileInput && (
            <LocalFileTab workspaceName={activeWorkspace.name} popStyle={popStyle} onFileUploaded={onFileUploaded}/>
          )}

          {websiteInput && (
            <UrlFileTab workspaceName={activeWorkspace.name} popStyle={popStyle} onFileUploaded={onFileUploaded}/>
          )}

          {rawTextInput && (
            <TextPasteTab workspaceName={activeWorkspace.name} popStyle={popStyle} onFileUploaded={onFileUploaded}/>
          )}

          <div className={popStyle["upload-options"]}>
            <button
              className={popStyle["upload-option"]}
              onClick={() => (
                setLocalFileInput(true),
                setWebsiteInput(false),
                setRawTextInput(false)
              )}
            >
              <div className={popStyle["upload-option-icon"]}>📂</div>
              <div className={popStyle["upload-option-title"]}>Upload</div>
            </button>
            <button
              className={popStyle["upload-option"]}
              onClick={() => (
                setWebsiteInput(true),
                setLocalFileInput(false),
                setRawTextInput(false)
              )}
            >
              <div className={popStyle["upload-option-icon"]}>🌐</div>
              <div className={popStyle["upload-option-title"]}>Website</div>
            </button>
            <button
              className={popStyle["upload-option"]}
              onClick={() => (
                setRawTextInput(true),
                setLocalFileInput(false),
                setWebsiteInput(false)
              )}
            >
              <div className={popStyle["upload-option-icon"]}>📋</div>
              <div className={popStyle["upload-option-title"]}>
                Paste the text
              </div>
            </button>
          </div>
        </div>

        <div className={popStyle["source-limit"]}>
          <span className={popStyle["limit-text"]}>Source limit</span>
          <span className={popStyle["limit-counter"]}>1/50</span>
        </div>
      </div>
    </div>
  );
}

export default UploadPopUp;
