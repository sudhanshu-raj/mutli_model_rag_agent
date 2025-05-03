import { logConfig, LogLevel } from "./logger.js";

console.log("node_env", process.env.NODE_ENV);
// Configure logging for different environments
if (process.env.NODE_ENV === 'production') {
  // Production settings
  logConfig.level = LogLevel.ERROR;      // Only log errors
  logConfig.enableRemote = true;         // Send logs to server
  logConfig.enableConsole = false;       // Disable console logs
  logConfig.includePayloads = false;     // Don't include sensitive data
} else if (process.env.NODE_ENV === 'test') {
  // Test environment settings
  logConfig.level = LogLevel.NONE;       // Disable all logging
  logConfig.enableRemote = false;      
} else {
  // Development settings
  logConfig.level = LogLevel.DEBUG;      // Log everything
  logConfig.enableRemote = true;         // temporarily enable remote logging
  logConfig.enableConsole = true;        // Enable console logs
}

// Import this file in your main app entry point
export default logConfig;