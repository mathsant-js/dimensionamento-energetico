import React, { useState, useEffect } from 'react';
import api from '../../api.ts';
import PropertyEditForm from './PropertyEditForm.tsx';
import PropertyDeleteModal from './PropertyDeleteModal.tsx';
import ConsumptionReport from './ConsumptionReport.tsx';
import { PropertyRead } from '../../types/property.ts';

interface PropertyListProps {
  token: string;
  refreshVersion: number;
  onChanged: () => void;
}

const PropertyList: React.FC<PropertyListProps> = ({ token, refreshVersion, onChanged }) => {
  const [properties, setProperties] = useState<PropertyRead[]>([]);
  const [deletingPropertyId, setDeletingPropertyId] = useState<number | null>(null);
  const [editingPropertyId, setEditingPropertyId] = useState<number | null>(null);
  const [viewingReportPropertyId, setViewingReportPropertyId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    const fetchProperties = async () => {
      try {
        const response = await api.get<PropertyRead[]>('/properties/', {
          headers: { Authorization: `Bearer ${token}` },
        });
        setProperties(response.data);
      } catch {
        setError('Não foi possível carregar as propriedades.');
      }
    };
    void fetchProperties();
  }, [token, refreshVersion]);

  const handleEdit = (propertyId: number) => {
    setEditingPropertyId(propertyId);
  };

  const handleDelete = (propertyId: number) => {
    setDeletingPropertyId(propertyId);
  };

  const handleDeleteCancel = () => {
    setDeletingPropertyId(null);
  };

  const handleViewReport = (propertyId: number) => {
    setViewingReportPropertyId(propertyId);
  };

  const confirmDelete = async () => {
    if (deletingPropertyId === null) return;
    setIsDeleting(true);
    setError(null);
    try {
      await api.delete(`/properties/${deletingPropertyId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setDeletingPropertyId(null);
      onChanged();
    } catch {
      setError('Não foi possível excluir a propriedade.');
    } finally {
      setIsDeleting(false);
    }
  };

  if (viewingReportPropertyId !== null) {
    const property = properties.find(p => p.id === viewingReportPropertyId);
    if (property) {
      return (
        <ConsumptionReport
          propertyId={viewingReportPropertyId}
          propertyName={property.identification}
          onClose={() => setViewingReportPropertyId(null)}
          token={token}
        />
      );
    }
  }

  return (
    <section>
      <div className="properties-header"><h2>Suas residências</h2><span className="eyebrow">{properties.length} cadastrada{properties.length === 1 ? '' : 's'}</span></div>
      {error && <p className="alert" role="alert">{error}</p>}
      {properties.length === 0 ? (
        <div className="empty-state">Nenhuma residência cadastrada ainda.<br />Use “Nova residência” para começar.</div>
      ) : (
        <ul className="property-list">
          {properties.map((property) => (
            <li className="property-card" key={property.id}>
              <div className="property-card-top">
              <div>
                <strong>{property.identification}</strong> ({property.property_type})
                <p className="property-meta">Perfil energético em preparação</p>
              </div>
              {editingPropertyId === property.id ? (
                <PropertyEditForm
                  property={property}
                  onSave={() => {
                    setEditingPropertyId(null);
                    onChanged();
                  }}
                  onCancel={() => setEditingPropertyId(null)}
                  token={token}
                />
              ) : (
                <>
                  <div className="card-actions"><button className="secondary-button" onClick={() => handleViewReport(property.id)}>Relatório</button>
                  <button className="secondary-button" onClick={() => handleEdit(property.id)}>Editar</button>
                  <button className="danger-button" onClick={() => handleDelete(property.id)}>Excluir</button></div>
                </>
              )}
              </div>
              {property.address && <p className="property-address">{property.address}{property.city ? `, ${property.city}` : ''}{property.state ? ` - ${property.state}` : ''}</p>}
              {deletingPropertyId === property.id && (
                <PropertyDeleteModal
                  onConfirm={confirmDelete}
                  onCancel={handleDeleteCancel}
                  isDeleting={isDeleting}
                />
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
};

export default PropertyList;
