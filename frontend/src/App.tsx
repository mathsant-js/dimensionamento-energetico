import React, { useState, useEffect } from "react";
import api from './api.ts';
import PropertyList from './components/properties/PropertyList.tsx';
import PropertyCreateForm from './components/properties/PropertyCreateForm.tsx';
import RegisterForm from './components/auth/RegisterForm.tsx';
import { PropertyCreate } from './types/property.ts';
import './App.css';

function App() {
  const [token, setToken] = useState<string | null>(null);
  const [loginError, setLoginError] = useState<string | null>(null);
  const [registerError, setRegisterError] = useState<string | null>(null);
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const [isRegistering, setIsRegistering] = useState(false);
  const [showRegisterForm, setShowRegisterForm] = useState(false);
  const [showCreatePropertyForm, setShowCreatePropertyForm] = useState(false);
  const [propertiesVersion, setPropertiesVersion] = useState(0);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

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
      const response = await api.post('/token', {
        email,
        password,
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

  const handleRegister = async (email: string, password: string, name: string) => {
    setIsRegistering(true);
    setRegisterError(null);
    try {
      await api.post('/users/', {
        email,
        password,
        name,
      });
      setShowRegisterForm(false);
      // Auto login after registration
      const loginResponse = await api.post('/token', {
        email,
        password,
      });
      const newToken = loginResponse.data.access_token;
      localStorage.setItem('token', newToken);
      setToken(newToken);
    } catch (error: any) {
      if (error.response?.data?.detail) {
        setRegisterError(error.response.data.detail);
      } else {
        setRegisterError('Registration failed');
      }
    } finally {
      setIsRegistering(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setToken(null);
  };

  const handleCreateProperty = async (propertyData: PropertyCreate) => {
    await api.post('/properties/', propertyData, {
      headers: { Authorization: `Bearer ${token}` },
    });
    setShowCreatePropertyForm(false);
    setPropertiesVersion((version) => version + 1);
  };

  if (!token) {
    return (
      <div className="App auth-shell">
        <main className="auth-card">
          <span className="eyebrow">Energia residencial</span>
          <h1>Seu espaço, sob controle.</h1>
          <p className="subtitle">Entre para organizar suas residências e preparar o dimensionamento energético.</p>
          {!showRegisterForm && (
            <button onClick={() => setShowRegisterForm(true)}>Criar conta</button>
          )}
          {showRegisterForm && (
            <RegisterForm
              onRegister={handleRegister}
              onCancel={() => setShowRegisterForm(false)}
              isRegistering={isRegistering}
              error={registerError}
            />
          )}
          {!showRegisterForm && (
            <div className="form-grid">
              {loginError && <p role="alert">{loginError}</p>}
              <div className="field full-width"><label htmlFor="login-email">E-mail</label><input
                id="login-email" type="email" placeholder="voce@exemplo.com"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
              /></div>
              <div className="field full-width"><label htmlFor="login-password">Senha</label><input
                id="login-password" type="password" placeholder="Sua senha"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
              /></div>
              <button
                onClick={() => handleLogin(email, password)}
                disabled={isLoggingIn}
              >
                {isLoggingIn ? 'Entrando...' : 'Entrar'}
              </button>
              <p className="auth-switch">Ainda não tem conta?<button className="link-button" onClick={() => setShowRegisterForm(true)}>Criar conta</button></p>
            </div>
          )}
        </main>
      </div>
    );
  }

  return (
    <div className="App app-shell">
      <header className="topbar">
        <div className="brand"><span className="brand-mark">E</span>Energia Clara</div>
        <div className="topbar-actions">
          <button className="secondary-button" onClick={handleLogout}>Sair</button>
          <button onClick={() => setShowCreatePropertyForm(true)}>Nova residência</button>
        </div>
      </header>
      <section className="dashboard-intro">
        <div><span className="eyebrow">Painel de residências</span><h1>Onde a sua energia começa.</h1></div>
        <p className="subtitle">Cadastre os espaços que farão parte da sua análise.</p>
      </section>
      {showCreatePropertyForm && (
        <PropertyCreateForm
          onCreate={handleCreateProperty}
          onCancel={() => setShowCreatePropertyForm(false)}
          isCreating={false}
        />
      )}
      <PropertyList 
        token={token} 
        refreshVersion={propertiesVersion}
        onChanged={() => setPropertiesVersion((version) => version + 1)}
      />
    </div>
  );
}

export default App;
