import { useState } from 'react'
import AppRoute from './routes'
import { AuthProvider } from './services/AuthContext'
import { BrowserRouter as Router } from 'react-router-dom'

function App() {
  const [count, setCount] = useState(0)

  return (
    <Router>
    <AuthProvider>
  <AppRoute />
    </AuthProvider>
    </Router>
  )
}

export default App
