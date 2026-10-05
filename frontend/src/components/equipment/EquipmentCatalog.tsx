import React, { useEffect, useState } from 'react';
import api from '../../api.ts';
import { Equipment } from '../../types/equipment.ts';

interface EquipmentCatalogProps {
  token: string;
}

const normalizeText = (value: string) => value
  .normalize('NFD')
  .replace(/[\u0300-\u036f]/g, '')
  .toLocaleLowerCase('pt-BR');

const EquipmentCatalog: React.FC<EquipmentCatalogProps> = ({ token }) => {
  const [equipments, setEquipments] = useState<Equipment[]>([]);
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchEquipments = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await api.get<Equipment[]>('/equipments/', {
          headers: { Authorization: `Bearer ${token}` },
        });
        setEquipments(response.data);
      } catch {
        setError('Não foi possível carregar o catálogo de equipamentos.');
      } finally {
        setIsLoading(false);
      }
    };

    void fetchEquipments();
  }, [token]);

  const categories = [...new Set(equipments.map((equipment) => equipment.category))]
    .sort((first, second) => first.localeCompare(second, 'pt-BR'));
  const normalizedSearch = normalizeText(search.trim());
  const visibleEquipments = equipments.filter((equipment) => (
    (!normalizedSearch || normalizeText(equipment.name).includes(normalizedSearch))
    && (!category || equipment.category === category)
  ));

  return (
    <section className="catalog-section" aria-labelledby="catalog-title">
      <div className="catalog-header">
        <div>
          <span className="eyebrow">Catálogo global</span>
          <h1 id="catalog-title">Equipamentos para consulta</h1>
          <p className="subtitle">Consulte potência e categoria dos equipamentos disponíveis para a sua análise.</p>
        </div>
        {!isLoading && <span className="eyebrow">{visibleEquipments.length} de {equipments.length} itens</span>}
      </div>

      <div className="catalog-filters">
        <div className="field">
          <label htmlFor="equipment-search">Buscar por nome</label>
          <input
            id="equipment-search"
            type="search"
            placeholder="Ex.: geladeira"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </div>
        <div className="field">
          <label htmlFor="equipment-category">Categoria</label>
          <select id="equipment-category" value={category} onChange={(event) => setCategory(event.target.value)}>
            <option value="">Todas as categorias</option>
            {categories.map((item) => <option key={item} value={item}>{item}</option>)}
          </select>
        </div>
      </div>

      {isLoading && <div className="empty-state" role="status">Carregando catálogo...</div>}
      {error && <p className="alert" role="alert">{error}</p>}
      {!isLoading && !error && visibleEquipments.length === 0 && (
        <div className="empty-state">Nenhum equipamento encontrado com os filtros informados.</div>
      )}
      {!isLoading && !error && visibleEquipments.length > 0 && (
        <ul className="equipment-list" aria-label="Equipamentos disponíveis">
          {visibleEquipments.map((equipment) => (
            <li className="equipment-card" key={equipment.id}>
              <div>
                <h2>{equipment.name}</h2>
                <p>{equipment.category}</p>
              </div>
              <strong>{equipment.power_watts} W</strong>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
};

export default EquipmentCatalog;
