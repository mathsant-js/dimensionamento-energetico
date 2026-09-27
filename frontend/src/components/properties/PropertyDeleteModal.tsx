import React from 'react';

interface PropertyDeleteModalProps {
  propertyId: number;
  onConfirm: () => void;
  onCancel: () => void;
  isDeleting: boolean;
}

const PropertyDeleteModal: React.FC<PropertyDeleteModalProps> = ({ onConfirm, onCancel, isDeleting }) => {
  return (
    <div className="modal-backdrop">
      <div className="modal" role="dialog" aria-modal="true" aria-labelledby="delete-title">
        <h3 id="delete-title">Excluir residência?</h3>
        <p>Tem certeza que deseja excluir esta propriedade?</p>
        <p>Esta ação não pode ser desfeita.</p>
        <div className="form-actions">
          <button className="secondary-button" onClick={onCancel} disabled={isDeleting}>Cancelar</button>
          <button className="danger-button" onClick={onConfirm} disabled={isDeleting}>
            {isDeleting ? 'Excluindo...' : 'Excluir'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default PropertyDeleteModal;
