import React, { useState, useEffect } from "react";
import axios from 'axios';
import PropertyList from './components/properties/PropertyList.tsx';
import './App.css';

function App() {
  const [token, setToken] = useState<string | null>(null);
  const [loginError, setLoginError] = useState<string | null>(null);
  const [isLoggingIn, setIsLoggingIn] = useState(false);

  // Try to get token from localStorage on initial load
  useEffect(() => {
    const storedToken = localStorage.getItem('token');
    if (storedToken) {
      setToken(storedToken);
    }
  }, []);

  const handleLogin = async (email: string, password: string) => {
    setIsLoggingIn(true);
    setLoginError(null);
    try {
      const response = await axios.post('/token', {
        email: email, // The API expects 'email' field
        password: password
      });
      const newToken = response.data.access_token;
      localStorage.setItem('token', newToken);
      setToken(newToken);
    } catch (error: any) {
      setLoginError('Invalid email or password');
    } finally {
      setIsLoggingIn(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setToken(null);
  };

  if (!token) {
    return (
      <div className="App">
        <header className="App-header">
          <h1>Login to Access Property Management</h1>
          {loginError && <p style={{ color: 'red' }}>{loginError}</p>}
          <div>
            <input
              type="email"
              placeholder="Email"
              id="login-email"
            />
            <br />
            <input
              type="password"
              placeholder="Password"
              id="login-password"
            />
            <br />
            <button
              onClick={() => {
                const email = (document.getElementById('login-email') as HTMLInputElement).value;
                const password = (document.getElementById('login-password') as HTMLInputElement).value;
                handleLogin(email, password);
              }}
              disabled={isLoggingIn}
            >
              {isLoggingIn ? 'Logging in...' : 'Login'}
            </button>
            <button onClick={handleLogout} style={{ marginLeft: '10px' }}>
              Logout
            </button>
          </div>
        </header>
      </div>
    );
  }

  return (
    <div className="App">
      <header className="App-header">
        <h1>Property Management System</h1>
        <button onClick={handleLogout}>Logout</button>
      </header>
      <PropertyList token={token} />
    </div>
  );
}

export default App;
