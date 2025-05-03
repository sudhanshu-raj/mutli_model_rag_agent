const extractFileName = (fileUrl) => {
    if (!fileUrl) return null;
    return decodeURIComponent(fileUrl.split("/").pop());
  };
  
  const getFileSize = async (fileUrl) => {
    try {
      const proxyUrl = "https://cors-anywhere.herokuapp.com/"; // Use a proxy to bypass CORS
      const response = await fetch(proxyUrl + encodeURIComponent(fileUrl), { method: "HEAD" });
  
      if (!response.ok) {
        throw new Error("Failed to fetch file metadata.");
      }
  
      const fileSize = response.headers.get("Content-Length");
  
      return fileSize ? formatBytes(parseInt(fileSize)) : "Unknown";
    } catch (error) {
      console.error("Error fetching file size:", error);
      return "Unknown"; // Fallback value
    }
  };
  
  const formatBytes = (bytes, decimals = 2) => {
    if (!bytes) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB", "TB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(decimals)) + " " + sizes[i];
  };
  

export const truncateFileName = (fileName, maxLength = 40) => {
  if (!fileName || fileName.length <= maxLength) {
    return fileName;
  }

  // Split the filename and extension
  const lastDotIndex = fileName.lastIndexOf('.');
  const extension = lastDotIndex !== -1 ? fileName.slice(lastDotIndex) : '';
  const name = lastDotIndex !== -1 ? fileName.slice(0, lastDotIndex) : fileName;

  const truncatedLength = maxLength - 3 - extension.length;
  
  // If truncatedLength is negative, the extension is too long
  if (truncatedLength <= 0) {
    return name.slice(0, maxLength - 3) + '...' + extension.slice(0, 5) + '...';
  }
  
  // Truncate the name and keep the extension
  return name.slice(0, truncatedLength) + '..., ' + extension;
};


export default {
    extractFileName,
    getFileSize,
    truncateFileName
  };
  