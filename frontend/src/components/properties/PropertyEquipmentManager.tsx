import React, { useEffect, useState } from 'react';
import api from '../../api.ts';
import { Equipment, PropertyEquipmentWithDetails } from '../../types/equipment.ts';

interface PropertyEquipmentManagerProps {
  propertyId: number;
  propertyName: string;
  token: string;
  onClose: () => void;
}

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

    setIsSaving(true);
    setError(null);
    try {
      const response = await api.post<PropertyEquipmentWithDetails>(
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
      setError(requestError.response?.status === 409
        ? 'Este equipamento já está vinculado a esta residência.'
        : 'Não foi possível adicionar o equipamento. Verifique os dados informados.');
    } finally {
      setIsSaving(false);
    }
  };

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
              <input id="equipment-quantity" type="number" min="1" step="1" required value={quantity} onChange={(event) => setQuantity(event.target.value)} />
            </div>
            <div className="field">
              <label htmlFor="equipment-hours">Horas de uso por dia</label>
              <input id="equipment-hours" type="number" min="0" max="24" step="0.1" required value={hoursPerDay} onChange={(event) => setHoursPerDay(event.target.value)} />
            </div>
          </div>
          <div className="form-actions"><button type="submit" disabled={isSaving || availableEquipments.length === 0}>{isSaving ? 'Adicionando...' : 'Adicionar equipamento'}</button></div>
        </form>

        <div className="properties-header"><h2>Equipamentos vinculados</h2><span className="eyebrow">{linkedEquipments.length} item{linkedEquipments.length === 1 ? '' : 's'}</span></div>
        {linkedEquipments.length === 0 ? (
          <div className="empty-state">Nenhum equipamento vinculado ainda.</div>
        ) : (
          <ul className="equipment-list">
            {linkedEquipments.map((item) => (
              <li className="equipment-card" key={item.id}>
                <div><h2>{item.equipment.name}</h2><p>{item.equipment.category} · {item.quantity} unidade{item.quantity === 1 ? '' : 's'} · {item.hours_per_day} h/dia</p></div>
                <strong>{item.equipment.power_watts} W</strong>
              </li>
            ))}
          </ul>
        )}
      </>}
    </section>
  );
};

export default PropertyEquipmentManager;
