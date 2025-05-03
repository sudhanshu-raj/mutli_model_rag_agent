import React from "react";
import { BrowserRouter as Router, Routes, Route,Navigate } from "react-router-dom";
import DashboardPage from "../pages/dashboardpage/InputDesign";
import LandingPage from "../pages/landingpage/InputDesign";
import ChatPage from "../pages/chatsection/Chat";
import PopUp from "../pages/chatsection/UploadPopUp";
import {AdminSignIn} from "../pages/auth/BasicLogin/SimpleLogin";
import { useAuth } from "../services/AuthContext";
import Loading from "../components/Loading"

const AppRoute =()=>{

    const { authenticated, isLoading } = useAuth()

    if (isLoading) {
        return <Loading /> 
    }


    return(
            <Routes>
                <Route path="/" element={<LandingPage />} />
                <Route path="/dashboard" 
                element={ authenticated ? <DashboardPage /> : <Navigate to ="/securitycheck" />} />
                <Route path="/chat" element={ authenticated ? <ChatPage /> : <Navigate to = "/securitycheck" />} />
                <Route path="/popup" element={<PopUp />} />
                <Route path="/securitycheck" element={authenticated ? <Navigate to ="/dashboard" />: <AdminSignIn />} />
            </Routes>
    )
}

export default AppRoute;