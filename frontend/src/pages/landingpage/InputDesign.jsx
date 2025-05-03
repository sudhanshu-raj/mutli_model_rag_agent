"use client";
import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import styles from "./InputDesign.module.css";
import { useAuth } from "../../services/AuthContext";

// Navbar Component
const Navbar = ({ isDarkMode, toggleDarkMode, scrolled }) => {
  const navigate = useNavigate();
  const { authenticated,logout } = useAuth();
  return (
    <nav
      className={styles.navbar}
      style={{
        backdropFilter: scrolled ? "blur(10px)" : "none",
        backgroundColor: scrolled
          ? isDarkMode
            ? "rgba(10, 10, 15, 0.8)"
            : "rgba(255, 255, 255, 0.8)"
          : "transparent",
      }}
    >
      <div className={styles.navbarContent}>
        <h1 className={styles.logo}>AI Notebook</h1>
        <div className={styles.navActions}>
          {/* <button
            className={styles.themeToggle}
            onClick={toggleDarkMode}
            aria-label={
              isDarkMode ? "Switch to light mode" : "Switch to dark mode"
            }
          >
            {isDarkMode ? <span>🌞</span> : <span>🌙</span>}
          </button> */}
          {authenticated ?( <button
            className={`${styles.ctaButton}`}
            onClick={() => navigate("/securitycheck")}
          >
            Logout
          </button>
          ) : (
            <button
              className={`${styles.ctaButton}`}
              onClick={logout}
            >
              Login
            </button>
          )}
        </div>
      </div>
    </nav>
  );
};

// Hero Section Component
const HeroSection = () => {
  const navigate = useNavigate();
  return (
    <section className={styles.heroSection}>
      <div className={styles.purpleOrb} aria-hidden="true" />
      <div className={styles.pinkOrb} aria-hidden="true" />
      <div className={styles.heroContent}>
        <h2 className={styles.heroTitle}>
          Your Intelligent Workspace for Smarter Thinking
        </h2>
        <p className={styles.heroDescription}>
          Transform your notes into intelligent conversations. Let AI help you
          organize, analyze, and enhance your thinking process.
        </p>
        <button
          className={`${styles.heroCta} ${styles.ctaButton}`}
          onClick={() => navigate("/dashboard")}
        >
          Start Your AI Notebook
        </button>
      </div>
    </section>
  );
};

// Feature Card Component
const FeatureCard = ({ icon, title, description, isDarkMode }) => {
  return (
    <article
      className={`${styles.featureCard}`}
      style={{
        background: isDarkMode
          ? "rgba(255, 255, 255, 0.05)"
          : "rgba(255, 255, 255, 0.8)",
      }}
    >
      <div className={styles.featureIcon} aria-hidden="true">
        {icon}
      </div>
      <h3 className={styles.featureTitle}>{title}</h3>
      <p className={styles.featureDescription}>{description}</p>
    </article>
  );
};

// Features Section Component
const FeaturesSection = ({ isDarkMode }) => {
  const features = [
    {
      title: "AI-Powered Analysis",
      description: "Get intelligent insights and suggestions from your notes",
      icon: "🤖",
    },
    {
      title: "Smart Organization",
      description: "Automatically categorize and structure your content",
      icon: "📊",
    },
    {
      title: "Real-time Collaboration",
      description: "Work together with team members seamlessly",
      icon: "👥",
    },
  ];

  return (
    <section
      className={styles.featuresSection}
      style={{
        background: isDarkMode ? "#12121a" : "#f8f9fa",
      }}
    >
      <div className={styles.featuresContainer}>
        <h2 className={styles.featuresTitle}>Powerful Features</h2>
        <div className={styles.featuresGrid}>
          {features.map((feature, index) => (
            <FeatureCard
              key={index}
              icon={feature.icon}
              title={feature.title}
              description={feature.description}
              isDarkMode={isDarkMode}
            />
          ))}
        </div>
      </div>
    </section>
  );
};

// Main Component
function LandingPage() {
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  function toggleDarkMode() {
    setIsDarkMode(!isDarkMode);
  }

  function toggleMenu() {
    setIsMenuOpen(!isMenuOpen);
  }

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 50);
    };

    window.addEventListener("scroll", handleScroll);

    return () => {
      window.removeEventListener("scroll", handleScroll);
    };
  }, []);

  return (
    <main
      className={styles.container}
      style={{
        backgroundColor: isDarkMode ? "#0a0a0f" : "#ffffff",
        color: isDarkMode ? "#ffffff" : "#0a0a0f",
      }}
    >
      <Navbar
        isDarkMode={isDarkMode}
        toggleDarkMode={toggleDarkMode}
        scrolled={scrolled}
      />
      <HeroSection />
      <FeaturesSection isDarkMode={isDarkMode} />
    </main>
  );
}

export default LandingPage;
