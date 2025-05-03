/**
 * Logger utility for application-wide logging
 * Supports console logs and server-side logging
 */

import { API_BASE_URL, ENDPOINTS } from "../api_calls/apiConfig";
import api from "../api_calls/axiosInterceptor"; // Import your axios instance

// Log levels
export const LogLevel = {
  DEBUG: 0,
  INFO: 1,
  WARN: 2,
  ERROR: 3,
  NONE: 4
};

// Default configuration
export const logConfig = {
  level: LogLevel.INFO,         // Default log level
  enableConsole: true,          // Log to browser console
  enableRemote: false,          // Send logs to server
  apiBaseUrl: API_BASE_URL,     // Base URL for API calls
  remoteEndpoint: ENDPOINTS.LOGS_UPLOAD,  // Server endpoint for logs
  includePayloads: true,        // Include data payloads in logs
  batchSize: 10,                // Send logs in batches
  appName: "NoteboolLM"         // Application name for logs
};

/**
 * Main logger class with static methods for different log levels
 */
export class Logger {
  static logQueue = [];
  static isSending = false;
  
  static formatTime() {
    return new Date().toISOString();
  }

  /**
   * Base log method that handles console output and remote logging
   */
  static log(level, message, data) {
    // Skip if log level is higher than configured
    if (this.getLevelValue(level) < logConfig.level) {
      return;
    }
    
    // Console logging
    if (logConfig.enableConsole) {
      const consoleMethod = 
        level === 'ERROR' ? console.error : 
        level === 'WARN' ? console.warn : 
        level === 'INFO' ? console.info : console.debug;
      
      consoleMethod(`[${this.formatTime()}] [${level}] ${message}`, data || '');
    }
    
    // Queue for server if enabled
    if (logConfig.enableRemote) {
      this.queueLog(level, message, data);
    }
  }
  
  /**
   * Convert string level to numeric value
   */
  static getLevelValue(levelString) {
    const map = {
      'DEBUG': LogLevel.DEBUG,
      'INFO': LogLevel.INFO,
      'WARN': LogLevel.WARN,
      'ERROR': LogLevel.ERROR
    };
    return map[levelString] || LogLevel.INFO;
  }
  
  // Convenience methods for different log levels
  static debug(message, data) { this.log('DEBUG', message, data); }
  static info(message, data) { this.log('INFO', message, data); }
  static warn(message, data) { this.log('WARN', message, data); }
  static error(message, data) { this.log('ERROR', message, data); }
  
  /**
   * Queue a log to be sent to the server
   */
  static queueLog(level, message, data) {
    const logEntry = {
      timestamp: this.formatTime(),
      level,
      message,
      application: logConfig.appName,
      data: logConfig.includePayloads ? data : undefined,
      user_id: localStorage.getItem('userId') || 'anonymous',
      session_id: sessionStorage.getItem('sessionId') || 'unknown',
      url: window.location.href,
      userAgent: navigator.userAgent
    };
    
    this.logQueue.push(logEntry);
    
    // Send logs if batch size reached
    if (this.logQueue.length >= logConfig.batchSize) {
      this.sendLogs();
    }
  }
  
  /**
   * Send queued logs to the server using axios instead of fetch
   */
  static async sendLogs() {
    if (this.isSending || this.logQueue.length === 0) return;
    
    this.isSending = true;
    const logsToSend = [...this.logQueue];
    this.logQueue = [];

    try {
      // Use axios interceptor instead of fetch
      await api.post(logConfig.remoteEndpoint, { logs: logsToSend });
    } catch (error) {
      console.error('Failed to send logs to server:', error);
      // Put logs back in queue if sending failed
      this.logQueue = [...logsToSend, ...this.logQueue];
    } finally {
      this.isSending = false;
      
      // If more logs accumulated while sending, send those too
      if (this.logQueue.length >= logConfig.batchSize) {
        setTimeout(() => this.sendLogs(), 1000);
      }
    }
  }
  
  /**
   * Force send all queued logs immediately
   */
  static flushLogs() {
    if (this.logQueue.length > 0) {
      this.sendLogs();
    }
  }
}

/**
 * API-specific logger with methods for tracking API calls
 * Updated to work better with axios responses
 */
export class ApiLogger extends Logger {
  /**
   * Log API request
   */
  static logRequest(endpoint, method, data) {
    this.info(`API Request: ${method} ${endpoint}`, 
      logConfig.includePayloads ? { payload: data } : null);
    return performance.now(); // Return start time for duration calculation
  }

  /**
   * Log API successful response
   */
  static logResponse(endpoint, status, data, startTime) {
    const duration = Math.round(performance.now() - startTime);
    this.info(`API Response: ${endpoint} (${status}) in ${duration}ms`, 
      logConfig.includePayloads ? { response: data } : null);
  }

  /**
   * Log API error - updated for axios error structure
   */
  static logError(endpoint, error, startTime) {
    const duration = startTime ? Math.round(performance.now() - startTime) : 0;
    this.error(`API Error: ${endpoint} in ${duration}ms`, {
      message: error.message,
      response: error.response?.data,
      status: error.response?.status
    });
  }
}

// Set up window unload handler to send pending logs
if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', () => Logger.flushLogs());
}

export default Logger;