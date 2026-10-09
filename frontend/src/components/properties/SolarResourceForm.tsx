import React, { FormEvent, useEffect, useState } from 'react';
import api from '../../api.ts';
import { SolarResource, SolarResourceInput } from '../../types/solarResource.ts';

interface SolarResourceFormProps {
  propertyId: number;
  propertyName: string;
  token: string;
  onClose: () => void;
}

const HSP_UNIT = 'kWh/m²/dia' as const;

const SolarResourceForm: React.FC<SolarResourceFormProps> = ({
  propertyId,
  propertyName,
  token,
  onClose,
}) => {
  const [hsp, setHsp] = useState('');
  const [source, setSource] = useState('Entrada manual confirmada pelo usuário');
  const [sourceDate, setSourceDate] = useState(new Date().toISOString().slice(0, 10));
  const [saved, setSaved] = useState<SolarResource | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await api.get<SolarResource>(
          `/properties/${propertyId}/solar-resource`,
          { headers: { Authorization: `Bearer ${token}` } },
        );
        setSaved(response.data);
        setHsp(response.data.hsp_kwh_m2_day);
        setSource(response.data.source);
        setSourceDate(response.data.source_date);
      } catch (requestError: any) {
        if (requestError.response?.status !== 404) {
          setError('Não foi possível carregar o recurso solar.');
        }
      } finally {
        setLoading(false);
      }
    };
    void load();
  }, [propertyId, token]);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    const numericHsp = Number(hsp);
    if (!Number.isFinite(numericHsp) || numericHsp <= 0) {
      setError('Informe um HSP maior que zero.');
      return;
    }
    if (!source.trim()) {
      setError('Informe a origem do valor de HSP.');
      return;
    }

    const payload: SolarResourceInput = {
      hsp_kwh_m2_day: numericHsp,
      unit: HSP_UNIT,
      source: source.trim(),
      source_date: sourceDate,
      acquisition_mode: 'manual',
    };
    setSaving(true);
    setError(null);
    try {
      const response = await api.put<SolarResource>(
        `/properties/${propertyId}/solar-resource`,
        payload,
        { headers: { Authorization: `Bearer ${token}` } },
      );
      setSaved(response.data);
      setHsp(response.data.hsp_kwh_m2_day);
    } catch (requestError: any) {
      const detail = requestError.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'Não foi possível confirmar o HSP.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <section className="solar-resource-section">
      <button className="secondary-button" onClick={onClose}>← Voltar</button>
      <div className="catalog-header">
        <div>
          <span className="eyebrow">Recurso solar</span>
          <h1>Confirmar HSP</h1>
          <p className="subtitle">{propertyName}</p>
        </div>
      </div>
      {loading ? <p className="empty-state">Carregando recurso solar...</p> : (
        <form className="form-card" onSubmit={submit}>
          <h3>Horas de Sol Pleno</h3>
          <p className="field-help">
            Nesta etapa o valor é manual. Nenhum HSP é estimado automaticamente a partir da localização.
          </p>
          {error && <p className="alert" role="alert">{error}</p>}
          <div className="form-grid">
            <div className="field">
              <label htmlFor="hsp-value">HSP ({HSP_UNIT})</label>
              <input
                id="hsp-value"
                type="number"
                min="0.001"
                step="0.001"
                required
                value={hsp}
                onChange={(event) => setHsp(event.target.value)}
              />
            </div>
            <div className="field">
              <label htmlFor="hsp-date">Data da origem</label>
              <input
                id="hsp-date"
                type="date"
                required
                value={sourceDate}
                onChange={(event) => setSourceDate(event.target.value)}
              />
            </div>
            <div className="field full-width">
              <label htmlFor="hsp-source">Origem</label>
              <input
                id="hsp-source"
                maxLength={500}
                required
                value={source}
                onChange={(event) => setSource(event.target.value)}
              />
            </div>
          </div>
          <div className="form-actions">
            <button type="button" className="secondary-button" onClick={onClose}>Cancelar</button>
            <button type="submit" disabled={saving}>{saving ? 'Confirmando...' : 'Confirmar HSP'}</button>
          </div>
          {saved && (
            <p className="success-message" role="status">
              HSP confirmado: <strong>{saved.hsp_kwh_m2_day} {saved.unit}</strong>, via entrada manual em {saved.source_date}.
            </p>
          )}
        </form>
      )}
    </section>
  );
};

export default SolarResourceForm;
