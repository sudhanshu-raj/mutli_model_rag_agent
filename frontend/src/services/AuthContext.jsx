import React, { createContext, useState, useContext, useEffect } from "react";
import axios from "axios";
import { ENDPOINTS } from "../api_calls/apiConfig";
import {
  getUserFromLocalStorage,
  removeUserFromLocalStorage,
  saveUserToLocalStorage,
} from "../utils/localstoragStuffs";
import { login } from "../pages/auth/BasicLogin/SimpleLogin";
import { useNavigate } from "react-router-dom";

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [authenticated, setAuthenticated] = useState(false); // default: not logged in
  const [isLoading, setIsLoading] = useState(true);
    const navigate = useNavigate();


  useEffect(() => {
    const authCheck = async () => {
      const user = getUserFromLocalStorage();
      if (user) {
        const authResponse = await login(user);
        if (authResponse.success) {
          setAuthenticated(true);
        } else {
          setAuthenticated(false);
        }
      } else {
        setAuthenticated(false);
      }
      setIsLoading(false);
    };
    authCheck();
  }, []);

  const logout = () => {
    setAuthenticated(false);
    removeUserFromLocalStorage();
    navigate("/securitycheck"); // Redirect to the login page after logout

  };

  const value = {
    authenticated,
    setAuthenticated,
    isLoading,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export default AuthContext;
