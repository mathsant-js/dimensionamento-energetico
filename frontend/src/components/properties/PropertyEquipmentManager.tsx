import React, { useEffect, useState } from 'react';
import api from '../../api.ts';
import { Equipment, PropertyEquipment, PropertyEquipmentWithDetails } from '../../types/equipment.ts';

interface PropertyEquipmentManagerProps {
  propertyId: number;
  propertyName: string;
  token: string;
  onClose: () => void;
}

const validateUsage = (quantity: string, hoursPerDay: string): string | null => {
  const parsedQuantity = Number(quantity);
  const parsedHours = Number(hoursPerDay);

  if (!Number.isInteger(parsedQuantity) || parsedQuantity <= 0) {
    return 'A quantidade deve ser um número inteiro maior que zero.';
  }
  if (!Number.isFinite(parsedHours) || parsedHours < 0 || parsedHours > 24) {
    return 'As horas de uso devem estar entre 0 e 24.';
  }
  return null;
};

const getRequestErrorMessage = (requestError: any, fallback: string) => {
  if (requestError.response?.status === 409) {
    return 'Este equipamento já está vinculado a esta residência.';
  }
  const detail = requestError.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) return detail.map((item) => item.msg).filter(Boolean).join(' ');
  return fallback;
};

const PropertyEquipmentManager: React.FC<PropertyEquipmentManagerProps> = ({
  propertyId,
  propertyName,
  token,
  onClose,
}) => {
  const [catalog, setCatalog] = useState<Equipment[]>([]);
  const [linkedEquipments, setLinkedEquipments] = useState<PropertyEquipmentWithDetails[]>([]);
  const [equipmentId, setEquipmentId] = useState('');
  const [quantity, setQuantity] = useState('1');
  const [hoursPerDay, setHoursPerDay] = useState('1');
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editingEquipmentId, setEditingEquipmentId] = useState<number | null>(null);
  const [editQuantity, setEditQuantity] = useState('');
  const [editHoursPerDay, setEditHoursPerDay] = useState('');
  const [removingEquipment, setRemovingEquipment] = useState<PropertyEquipmentWithDetails | null>(null);
  const [isRemoving, setIsRemoving] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const headers = { Authorization: `Bearer ${token}` };
        const [catalogResponse, linkedResponse] = await Promise.all([
          api.get<Equipment[]>('/equipments/', { headers }),
          api.get<PropertyEquipmentWithDetails[]>(`/properties/${propertyId}/equipments/`, { headers }),
        ]);
        setCatalog(catalogResponse.data);
        setLinkedEquipments(linkedResponse.data);
      } catch {
        setError('Não foi possível carregar os equipamentos da residência.');
      } finally {
        setIsLoading(false);
      }
    };

    void fetchData();
  }, [propertyId, token]);

  const linkedEquipmentIds = new Set(linkedEquipments.map((item) => item.equipment_id));
  const availableEquipments = catalog.filter((equipment) => !linkedEquipmentIds.has(equipment.id));

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!equipmentId) {
      setError('Selecione um equipamento para adicionar.');
      return;
    }
    const validationError = validateUsage(quantity, hoursPerDay);
    if (validationError) {
      setError(validationError);
      return;
    }

    setIsSaving(true);
    setError(null);
    try {
      const response = await api.post<PropertyEquipment>(
        `/properties/${propertyId}/equipments/`,
        {
          equipment_id: Number(equipmentId),
          quantity: Number(quantity),
          hours_per_day: Number(hoursPerDay),
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      const equipment = catalog.find((item) => item.id === response.data.equipment_id);
      if (equipment) {
        setLinkedEquipments((items) => [...items, { ...response.data, equipment }]);
      }
      setEquipmentId('');
      setQuantity('1');
      setHoursPerDay('1');
    } catch (requestError: any) {
      setError(getRequestErrorMessage(requestError, 'Não foi possível adicionar o equipamento.'));
    } finally {
      setIsSaving(false);
    }
  };

  const startEditing = (item: PropertyEquipmentWithDetails) => {
    setError(null);
    setEditingEquipmentId(item.id);
    setEditQuantity(String(item.quantity));
    setEditHoursPerDay(String(item.hours_per_day));
  };

  const cancelEditing = () => {
    setEditingEquipmentId(null);
    setEditQuantity('');
    setEditHoursPerDay('');
  };

  const handleUpdate = async (event: React.FormEvent<HTMLFormElement>, item: PropertyEquipmentWithDetails) => {
    event.preventDefault();
    const validationError = validateUsage(editQuantity, editHoursPerDay);
    if (validationError) {
      setError(validationError);
      return;
    }

    setIsSaving(true);
    setError(null);
    try {
      const response = await api.put<PropertyEquipment>(
        `/properties/${propertyId}/equipments/${item.id}`,
        { quantity: Number(editQuantity), hours_per_day: Number(editHoursPerDay) },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setLinkedEquipments((items) => items.map((linkedItem) => (
        linkedItem.id === item.id ? { ...linkedItem, ...response.data } : linkedItem
      )));
      cancelEditing();
    } catch (requestError: any) {
      setError(getRequestErrorMessage(requestError, 'Não foi possível atualizar o equipamento.'));
    } finally {
      setIsSaving(false);
    }
  };

  const confirmRemoval = async () => {
    if (!removingEquipment) return;

    setIsRemoving(true);
    setError(null);
    try {
      await api.delete(`/properties/${propertyId}/equipments/${removingEquipment.id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setLinkedEquipments((items) => items.filter((item) => item.id !== removingEquipment.id));
      setRemovingEquipment(null);
    } catch (requestError: any) {
      setError(getRequestErrorMessage(requestError, 'Não foi possível remover o equipamento.'));
    } finally {
      setIsRemoving(false);
    }
  };

  const getMonthlyConsumption = (item: PropertyEquipmentWithDetails) => (
    (item.equipment.power_watts * item.quantity * item.hours_per_day * 30) / 1000
  );

  return (
    <section className="equipment-manager" aria-labelledby="equipment-manager-title">
      <div className="properties-header">
        <div>
          <span className="eyebrow">{propertyName}</span>
          <h1 id="equipment-manager-title">Gerenciar equipamentos</h1>
        </div>
        <button className="secondary-button" onClick={onClose}>Voltar</button>
      </div>
      <p className="subtitle">Selecione itens do catálogo global para compor o consumo desta residência.</p>

      {error && <p className="alert" role="alert">{error}</p>}
      {isLoading ? <div className="empty-state" role="status">Carregando equipamentos...</div> : <>
        <form className="form-card equipment-link-form" onSubmit={handleSubmit}>
          <h2>Adicionar equipamento</h2>
          <div className="form-grid">
            <div className="field full-width">
              <label htmlFor="property-equipment">Equipamento</label>
              <select id="property-equipment" value={equipmentId} onChange={(event) => setEquipmentId(event.target.value)} disabled={availableEquipments.length === 0}>
                <option value="">{availableEquipments.length === 0 ? 'Todos os itens já foram vinculados' : 'Selecione um item do catálogo'}</option>
                {availableEquipments.map((equipment) => (
                  <option key={equipment.id} value={equipment.id}>{equipment.name} - {equipment.category} ({equipment.power_watts} W)</option>
                ))}
              </select>
            </div>
            <div className="field">
              <label htmlFor="equipment-quantity">Quantidade</label>
              <input id="equipment-quantity" type="number" min="1" step="1" required value={quantity} onChange={(event) => setQuantity(event.target.value)} aria-describedby="usage-help" />
            </div>
            <div className="field">
              <label htmlFor="equipment-hours">Horas de uso por dia</label>
              <input id="equipment-hours" type="number" min="0" max="24" step="0.1" required value={hoursPerDay} onChange={(event) => setHoursPerDay(event.target.value)} aria-describedby="usage-help" />
            </div>
          </div>
          <p id="usage-help" className="field-help">Quantidade deve ser inteira e maior que zero. As horas podem variar de 0 a 24.</p>
          <div className="form-actions"><button type="submit" disabled={isSaving || availableEquipments.length === 0}>{isSaving ? 'Adicionando...' : 'Adicionar equipamento'}</button></div>
        </form>

        <div className="properties-header"><h2>Equipamentos vinculados</h2><span className="eyebrow">{linkedEquipments.length} item{linkedEquipments.length === 1 ? '' : 's'}</span></div>
        {linkedEquipments.length === 0 ? (
          <div className="empty-state">Nenhum equipamento vinculado ainda.</div>
        ) : (
          <ul className="equipment-list">
            {linkedEquipments.map((item) => (
              <li className={`equipment-card ${editingEquipmentId === item.id ? 'equipment-card-editing' : ''}`} key={item.id}>
                {editingEquipmentId === item.id ? (
                  <form className="equipment-edit-form" onSubmit={(event) => handleUpdate(event, item)}>
                    <div><h2>{item.equipment.name}</h2><p>{item.equipment.category}</p></div>
                    <div className="equipment-edit-fields">
                      <label>Quantidade<input type="number" min="1" step="1" required value={editQuantity} onChange={(event) => setEditQuantity(event.target.value)} /></label>
                      <label>Horas/dia<input type="number" min="0" max="24" step="0.1" required value={editHoursPerDay} onChange={(event) => setEditHoursPerDay(event.target.value)} /></label>
                    </div>
                    <div className="card-actions"><button type="button" className="secondary-button" onClick={cancelEditing} disabled={isSaving}>Cancelar</button><button type="submit" disabled={isSaving}>{isSaving ? 'Salvando...' : 'Salvar'}</button></div>
                  </form>
                ) : <>
                  <div>
                    <h2>{item.equipment.name}</h2>
                    <p>{item.equipment.category} · {item.quantity} unidade{item.quantity === 1 ? '' : 's'} · {item.hours_per_day} h/dia</p>
                    <p className="equipment-consumption">{getMonthlyConsumption(item).toLocaleString('pt-BR', { maximumFractionDigits: 2 })} kWh/mês estimados</p>
                  </div>
                  <div className="equipment-card-actions">
                    <strong>{item.equipment.power_watts} W</strong>
                    <div className="equipment-card-controls"><button className="secondary-button" onClick={() => startEditing(item)}>Editar uso</button><button className="danger-button" onClick={() => setRemovingEquipment(item)}>Remover</button></div>
                  </div>
                </>}
              </li>
            ))}
          </ul>
        )}
      </>}
      {removingEquipment && (
        <div className="modal-backdrop" role="presentation">
          <div className="modal" role="dialog" aria-modal="true" aria-labelledby="remove-equipment-title">
            <h3 id="remove-equipment-title">Remover equipamento?</h3>
            <p>{removingEquipment.equipment.name} deixará de compor o consumo desta residência.</p>
            <div className="form-actions">
              <button className="secondary-button" onClick={() => setRemovingEquipment(null)} disabled={isRemoving}>Cancelar</button>
              <button className="danger-button" onClick={confirmRemoval} disabled={isRemoving}>{isRemoving ? 'Removendo...' : 'Remover'}</button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
};

export default PropertyEquipmentManager;
