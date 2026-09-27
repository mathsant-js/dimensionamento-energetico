import React, { useState } from 'react';

interface RegisterFormProps {
  onRegister: (email: string, password: string, name: string) => void;
  onCancel: () => void;
  isRegistering?: boolean;
  error?: string | null;
}

const RegisterForm: React.FC<RegisterFormProps> = ({ onRegister, onCancel, isRegistering = false, error = null }) => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});

    try {
      await onRegister(formData.email, formData.password, formData.name);
    } catch (error: any) {
      if (error.response?.data?.detail) {
        // Handle validation errors
        if (typeof error.response.data.detail === 'string') {
          setErrors({ submit: error.response.data.detail });
        } else {
          // Assuming it's an array of validation errors
          const errorMap: Record<string, string> = {};
          error.response.data.detail.forEach((err: any) => {
            if (err.loc && err.loc.length > 1) {
              const fieldName = err.loc[err.loc.length - 1];
              errorMap[fieldName as string] = err.msg;
            }
          });
          setErrors(errorMap);
        }
      } else {
        setErrors({ submit: 'Registration failed' });
      }
    }
  };

  return (
    <div className="form-card">
      <h3>Crie sua conta</h3>
      <p className="subtitle">Comece a mapear o consumo das suas residências.</p>
      <form className="form-grid" onSubmit={handleSubmit}>
        <div>
          <label>Name:</label>
          <input
            type="text"
            name="name"
            value={formData.name}
            onChange={handleChange}
            required
          />
          {errors.name && <span style={{ color: 'red' }}>{errors.name}</span>}
        </div>
        
        <div>
          <label>Email:</label>
          <input
            type="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            required
          />
          {errors.email && <span style={{ color: 'red' }}>{errors.email}</span>}
        </div>
        
        <div>
          <label>Password:</label>
          <input
            type="password"
            name="password"
            value={formData.password}
            onChange={handleChange}
            required
          />
          {errors.password && <span style={{ color: 'red' }}>{errors.password}</span>}
        </div>
        
        {Object.keys(errors).length > 0 && (
          <div style={{ color: 'red', margin: '10px 0' }}>
            Por favor, corrija os erros no formulário.
          </div>
        )}
        {error && <p role="alert">{error}</p>}
        
        <div className="form-actions full-width">
          <button type="submit" disabled={isRegistering}>
            {isRegistering ? 'Criando...' : 'Criar conta'}
          </button>
          <button type="button" onClick={onCancel} style={{ marginLeft: '8px' }}>
            Cancelar
          </button>
        </div>
      </form>
    </div>
  );
};

export default RegisterForm;
