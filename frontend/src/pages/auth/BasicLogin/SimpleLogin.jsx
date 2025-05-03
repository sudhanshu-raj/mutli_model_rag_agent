
import { useState ,useNavigate} from "react"
import { Shield, Lock, Unlock, Key } from "lucide-react"
import styles from "./SimpleLogin.module.css"
import axios from "axios"
import { ENDPOINTS } from "../../../api_calls/apiConfig"
import { useAuth } from "../../../services/AuthContext"
import { saveUserToLocalStorage } from "../../../utils/localstoragStuffs"


const login = async (user) => {
  try {
    const response = await axios.post(ENDPOINTS.AUTH_LOGIN, user)
    console.log(response.data)
    return {
      success: true,
      data: response.data,  
    }
  }
  catch (error) {
    console.error("Error during login:", error)
    if (error.response?.data) {
      return {
          success: false,
          error: error.response.data,
      };
  }
  return {
      success: false,
      error: error.message || "Failed to login",
  };
  }
}

function AdminSignIn() {

  const { setAuthenticated } = useAuth()

  const [password, setPassword] = useState("")
  const [isShaking, setIsShaking] = useState(false)
  const [isUnlocking, setIsUnlocking] = useState(false)
  const [isUnlocked, setIsUnlocked] = useState(false)


  const handleSubmit = async (e) => {
    e.preventDefault()

    const user = {
      "secret_key": password,
    }

    const loginResponse = await login(user)
    if (loginResponse.success) {
      setIsUnlocking(true)
      

      setTimeout(() => {
        setIsUnlocked(true)
        setIsUnlocking(false)
        saveUserToLocalStorage(user) // Save user data to local storage with a  default TTL 
        setAuthenticated(true) 

      }, 2000)
    } else {
      setIsShaking(true)
      setTimeout(() => setIsShaking(false), 500)
    }
    
  }

  return (
    <div className={styles.container}>
      <div className={styles.vault}>
        <div className={`${styles.securityGuard} ${isShaking ? styles.shake : ""}`}>
          <Shield className={styles.shield} size={40} />
          <div className={styles.face}>
            <div className={styles.eyes}></div>
            <div className={styles.mouth}></div>
          </div>
        </div>

        <div className={styles.lockContainer}>
          {isUnlocked ? (
            <Unlock className={styles.unlocked} size={60} />
          ) : isUnlocking ? (
            <div className={styles.unlocking}>
              <Lock className={styles.lock} size={60} />
            </div>
          ) : (
            <Lock className={styles.lock} size={60} />
          )}
        </div>

        {isUnlocked ? (
          <div className={styles.successMessage}>
            <h2>Access Granted</h2>
            <p>Welcome to the admin panel</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className={styles.form}>
            <h1>Secure Admin Access</h1>
            <p className={styles.instruction}>Enter the secret key to proceed</p>

            <div className={styles.inputGroup}>
              <Key size={20} className={styles.inputIcon} />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter secret key"
                className={styles.input}
                required
              />
            </div>

            <button type="submit" className={styles.submitButton}>
              Verify Identity
            </button>
          </form>
        )}
      </div>
    </div>
  )
}

export {
  AdminSignIn,
  login
}