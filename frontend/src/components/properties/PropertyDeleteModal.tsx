import React from 'react';

interface PropertyDeleteModalProps {
  propertyId: number;
  onConfirm: () => void;
  onCancel: () => void;
}

const PropertyDeleteModal: React.FC<PropertyDeleteModalProps> = ({ propertyId, onConfirm, onCancel }) => {
  return (
    <div style={{ 
      position: 'fixed', 
      top: 0, 
      left: 0, 
      right: 0, 
      bottom: 0, 
      backgroundColor: 'rgba(0,0,0,0.5)', 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'center',
      zIndex: 1000 
    }}>
      <div style={{ 
        backgroundColor: 'white', 
        padding: '24px', 
        borderRadius: '8px', 
        width: '300px' 
      }}>
        <h3>Confirmação de Exclusão</h3>
        <p>Tem certeza que deseja excluir esta propriedade?</p>
        <p>Esta ação não pode ser desfeita.</p>
        <div style={{ marginTop: '20px', display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
          <button onClick={onCancel}>Cancelar</button>
          <button onClick={onConfirm} style={{ backgroundColor: '#dc3545', color: 'white', border: 'none' }}>
            Excluir
          </button>
        </div>
      </div>
    </div>
  );
};

export default PropertyDeleteModal;
