import React, { useState, useEffect } from 'react';
import axios from 'axios';
import PropertyEditForm from './PropertyEditForm';
import PropertyDeleteModal from './PropertyDeleteModal';
import { PropertyRead } from '../../types/property';

interface PropertyListProps {
  token: string;
}

const PropertyList: React.FC<PropertyListProps> = ({ token }) => {
  const [properties, setProperties] = useState<PropertyRead[]>([]);
  const [editingPropertyId, setEditingPropertyId] = useState<number | null>(null);
  const [deletingPropertyId, setDeletingPropertyId] = useState<number | null>(null);

  useEffect(() => {
    const fetchProperties = async () => {
      try {
        const response = await axios.get<PropertyRead[]>('/properties/', {
          headers: { Authorization: `Bearer ${token}` },
        });
        setProperties(response.data);
      } catch (error) {
        console.error('Error fetching properties:', error);
      }
    };

    fetchProperties();
  }, [token]);

  const handleEdit = (propertyId: number) => {
    setEditingPropertyId(propertyId);
  };

  const handleDelete = (propertyId: number) => {
    setDeletingPropertyId(propertyId);
  };

  const handleEditCancel = () => {
    setEditingPropertyId(null);
  };

  const handleDeleteCancel = () => {
    setDeletingPropertyId(null);
  };

  return (
    <div>
      <h2>Minhas Propriedades</h2>
      {properties.length === 0 ? (
        <p>Você ainda não possui propriedades cadastradas.</p>
      ) : (
        <ul>
          {properties.map((property) => (
            <li key={property.id}>
              <div>
                <strong>{property.identification}</strong> ({property.property_type})
              </div>
              {editingPropertyId === property.id ? (
                <PropertyEditForm
                  property={property}
                  onSave={() => {
                    setEditingPropertyId(null);
                    // Refetch properties after edit (optional, but we can do it)
                    // For simplicity, we'll refetch after a short delay or rely on the update in the list via state
                    // We'll refetch to be safe
                    fetchProperties();
                  }}
                  onCancel={handleEditCancel}
                />
              ) : (
                <>
                  <button onClick={() => handleEdit(property.id)}>Editar</button>
                  <button onClick={() => handleDelete(property.id)}>Excluir</button>
                </>
              )}
              {deletingPropertyId === property.id && (
                <PropertyDeleteModal
                  propertyId={property.id}
                  onConfirm={() => {
                    setDeletingPropertyId(null);
                    // Refetch after deletion
                    fetchProperties();
                  }}
                  onCancel={handleDeleteCancel}
                />
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default PropertyList;
