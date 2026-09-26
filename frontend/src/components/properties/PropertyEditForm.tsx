import React, { useState } from 'react';
import axios from 'axios';
import { PropertyUpdate, PropertyRead } from '../../types/property';

interface PropertyEditFormProps {
  property: PropertyRead;
  onSave: () => void;
  onCancel: () => void;
}

const PropertyEditForm: React.FC<PropertyEditFormProps> = ({ property, onSave, onCancel }) => {
  const [formData, setFormData] = useState<PropertyUpdate>({
    identification: property.identification,
    property_type: property.property_type,
    address: property.address || '',
    city: property.city || '',
    state: property.state || '',
    zipcode: property.zipcode || '',
    latitude: property.latitude ? String(property.latitude) : '',
    longitude: property.longitude ? String(property.longitude) : '',
    built_area: property.built_area ? String(property.built_area) : '',
    roof_area: property.roof_area ? String(property.roof_area) : '',
    orientation: property.orientation || '',
    tilt_angle: property.tilt_angle ? String(property.tilt_angle) : '',
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value === '' ? undefined : value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});
    setLoading(true);

    try {
      // Filter out undefined values
      const updateData = Object.entries(formData)
        .filter(([, value]) => value !== undefined && value !== '')
        .reduce((obj, [key, value]) => ({
          ...obj,
          [key]: value,
        }), {} as PropertyUpdate);

      await axios.put(`/properties/${property.id}`, updateData, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
      });
      onSave();
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
        setErrors({ submit: 'An unexpected error occurred' });
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ border: '1px solid #ccc', padding: '16px', margin: '16px 0' }}>
      <h3>Editar Propriedade</h3>
      <form onSubmit={handleSubmit}>
        <div>
          <label>Identificação:</label>
          <input
            type="text"
            name="identification"
            value={formData.identification || ''}
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
            value={formData.property_type || ''}
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
            value={formData.address || ''}
            onChange={handleChange}
          />
        </div>
        
        <div>
          <label>Cidade:</label>
          <input
            type="text"
            name="city"
            value={formData.city || ''}
            onChange={handleChange}
          />
        </div>
        
        <div>
          <label>Estado:</label>
          <input
            type="text"
            name="state"
            value={formData.state || ''}
            onChange={handleChange}
          />
        </div>
        
        <div>
          <label>CEP:</label>
          <input
            type="text"
            name="zipcode"
            value={formData.zipcode || ''}
            onChange={handleChange}
          />
        </div>
        
        <div>
          <label>Latitude:</label>
          <input
            type="number"
            step="any"
            name="latitude"
            value={formData.latitude || ''}
            onChange={handleChange}
          />
        </div>
        
        <div>
          <label>Longitude:</label>
          <input
            type="number"
            step="any"
            name="longitude"
            value={formData.longitude || ''}
            onChange={handleChange}
          />
        </div>
        
        <div>
          <label>Área Construída (m²):</label>
          <input
            type="number"
            step="any"
            name="built_area"
            value={formData.built_area || ''}
            onChange={handleChange}
          />
        </div>
        
        <div>
          <label>Área do Telhado (m²):</label>
          <input
            type="number"
            step="any"
            name="roof_area"
            value={formData.roof_area || ''}
            onChange={handleChange}
          />
        </div>
        
        <div>
          <label>Orientação:</label>
          <input
            type="text"
            name="orientation"
            value={formData.orientation || ''}
            onChange={handleChange}
          />
        </div>
        
        <div>
          <label>Ângulo de Inclinação (graus):</label>
          <input
            type="number"
            step="any"
            name="tilt_angle"
            value={formData.tilt_angle || ''}
            onChange={handleChange}
          />
        </div>
        
        {Object.keys(errors).length > 0 && (
          <div style={{ color: 'red', margin: '10px 0' }}>
            Por favor, corrija os erros no formulário.
          </div>
        )}
        
        <div style={{ marginTop: '16px' }}>
          <button type="submit" disabled={loading}>
            {loading ? 'Salvando...' : 'Salvar'}
          </button>
          <button type="button" onClick={onCancel} style={{ marginLeft: '8px' }}>
            Cancelar
          </button>
        </div>
      </form>
    </div>
  );
};

export default PropertyEditForm;
