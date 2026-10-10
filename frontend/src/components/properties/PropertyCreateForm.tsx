import React, { useState } from 'react';
import { PropertyCreate } from '../../types/property.ts';

interface PropertyCreateFormProps {
  onCreate: (propertyData: PropertyCreate) => Promise<void>;
  onCancel: () => void;
  isCreating?: boolean;
}

const PropertyCreateForm: React.FC<PropertyCreateFormProps> = ({ onCreate, onCancel, isCreating = false }) => {
  const [formData, setFormData] = useState({
    identification: '',
    property_type: '',
    address: '',
    city: '',
    state: '',
    zipcode: '',
    latitude: '',
    longitude: '',
    built_area: '',
    roof_area: '',
    orientation: '',
    tilt_angle: '',
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);

  const validatePropertyForm = () => {
    const nextErrors: Record<string, string> = {};

    const identification = formData.identification.trim();
    const propertyType = formData.property_type.trim();

    if (!identification) {
      nextErrors.identification = 'A identificação do imóvel é obrigatória.';
    } else if (identification.length < 2) {
      nextErrors.identification = 'A identificação deve ter pelo menos 2 caracteres.';
    }

    if (!propertyType) {
      nextErrors.property_type = 'O tipo do imóvel é obrigatório.';
    } else if (propertyType.length < 2) {
      nextErrors.property_type = 'O tipo do imóvel deve ter pelo menos 2 caracteres.';
    }

    const numericFields: Array<[string, string, 'positive' | 'nonNegative' | 'latitude' | 'longitude' | 'tiltAngle']> = [
      ['latitude', formData.latitude, 'latitude'],
      ['longitude', formData.longitude, 'longitude'],
      ['built_area', formData.built_area, 'positive'],
      ['roof_area', formData.roof_area, 'nonNegative'],
      ['tilt_angle', formData.tilt_angle, 'tiltAngle'],
    ];

    numericFields.forEach(([field, value, mode]) => {
      if (!value) return;

      const parsed = Number(value);
      if (Number.isNaN(parsed)) {
        nextErrors[field] = 'Informe um valor numérico válido.';
        return;
      }

      if (mode === 'positive' && parsed <= 0) {
        nextErrors[field] = 'A área construída deve ser maior que zero.';
      }

      if (mode === 'nonNegative' && parsed < 0) {
        nextErrors[field] = 'A área do telhado não pode ser negativa.';
      }

      if (mode === 'latitude' && (parsed < -90 || parsed > 90)) {
        nextErrors[field] = 'A latitude deve estar entre -90 e 90.';
      }

      if (mode === 'longitude' && (parsed < -180 || parsed > 180)) {
        nextErrors[field] = 'A longitude deve estar entre -180 e 180.';
      }

      if (mode === 'tiltAngle' && (parsed < 0 || parsed > 90)) {
        nextErrors[field] = 'O ângulo de inclinação deve estar entre 0° e 90°.';
      }
    });

    setErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
    setErrors(prev => ({
      ...prev,
      [name]: '',
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validatePropertyForm()) {
      return;
    }
    setLoading(true);

    try {
      // Prepare data for API (convert empty strings to undefined for optional fields)
      const propertyData: PropertyCreate = {
        identification: formData.identification.trim(),
        property_type: formData.property_type.trim(),
        address: formData.address?.trim() || undefined,
        city: formData.city?.trim() || undefined,
        state: formData.state?.trim() || undefined,
        zipcode: formData.zipcode?.trim() || undefined,
        latitude: formData.latitude ? parseFloat(formData.latitude) : undefined,
        longitude: formData.longitude ? parseFloat(formData.longitude) : undefined,
        built_area: formData.built_area ? parseFloat(formData.built_area) : undefined,
        roof_area: formData.roof_area ? parseFloat(formData.roof_area) : undefined,
        orientation: formData.orientation?.trim() || undefined,
        tilt_angle: formData.tilt_angle ? parseFloat(formData.tilt_angle) : undefined,
      };

      await onCreate(propertyData);
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
        setErrors({ submit: 'Ocorreu um erro inesperado.' });
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="form-card">
      <h3>Nova residência</h3>
      <p className="subtitle">Informe os detalhes disponíveis para criar o perfil do imóvel.</p>
      <form className="form-grid" onSubmit={handleSubmit}>
        <div>
          <label>Identificação:</label>
          <input
            type="text"
            name="identification"
            value={formData.identification}
            onChange={handleChange}
            required
          />
          {errors.identification && <span style={{ color: 'red' }}>{errors.identification}</span>}
        </div>
        
        <div>
          <label>Tipo:</label>
          <input
            type="text"
            name="property_type"
            value={formData.property_type}
            onChange={handleChange}
            required
          />
          {errors.property_type && <span style={{ color: 'red' }}>{errors.property_type}</span>}
        </div>
        
        <div>
          <label>Endereço:</label>
          <input
            type="text"
            name="address"
            value={formData.address}
            onChange={handleChange}
          />
        </div>
        
        <div>
          <label>Cidade:</label>
          <input
            type="text"
            name="city"
            value={formData.city}
            onChange={handleChange}
          />
        </div>
        
        <div>
          <label>Estado:</label>
          <input
            type="text"
            name="state"
            value={formData.state}
            onChange={handleChange}
          />
        </div>
        
        <div>
          <label>CEP:</label>
          <input
            type="text"
            name="zipcode"
            value={formData.zipcode}
            onChange={handleChange}
          />
        </div>
        
        <div>
          <label>Latitude:</label>
          <input
            type="number"
            step="any"
            min={-90}
            max={90}
            name="latitude"
            value={formData.latitude}
            onChange={handleChange}
          />
        </div>
        
        <div>
          <label>Longitude:</label>
          <input
            type="number"
            step="any"
            min={-180}
            max={180}
            name="longitude"
            value={formData.longitude}
            onChange={handleChange}
          />
        </div>
        
        <div>
          <label>Área Construída (m²):</label>
          <input
            type="number"
            step="any"
            min={0}
            name="built_area"
            value={formData.built_area}
            onChange={handleChange}
          />
        </div>
        
        <div>
          <label>Área do Telhado (m²):</label>
          <input
            type="number"
            step="any"
            min={0}
            name="roof_area"
            value={formData.roof_area}
            onChange={handleChange}
          />
        </div>
        
        <div>
          <label>Orientação:</label>
          <input
            type="text"
            name="orientation"
            value={formData.orientation}
            onChange={handleChange}
          />
        </div>
        
        <div>
          <label>Ângulo de Inclinação (graus):</label>
          <input
            type="number"
            step="any"
            min={0}
            max={90}
            name="tilt_angle"
            value={formData.tilt_angle}
            onChange={handleChange}
          />
        </div>
        
        {Object.keys(errors).length > 0 && (
          <div style={{ color: 'red', margin: '10px 0' }}>
            Por favor, corrija os erros no formulário.
          </div>
        )}
        
        <div className="form-actions full-width">
          <button type="submit" disabled={loading}>
            {loading ? 'Criando...' : 'Criar Propriedade'}
          </button>
          <button className="secondary-button" type="button" onClick={onCancel}>
            Cancelar
          </button>
        </div>
      </form>
    </div>
  );
};

export default PropertyCreateForm;
