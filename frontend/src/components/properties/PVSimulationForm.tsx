import React, { FormEvent, useEffect, useState } from 'react';
import api from '../../api.ts';
import { ConsumptionReport } from '../../types/equipment.ts';
import { PVBatteryCatalogItem, PVProposal, PVSimulation, PVSimulationRequest } from '../../types/pv.ts';
import { SolarResource } from '../../types/solarResource.ts';

interface PVSimulationFormProps {
  propertyId: number;
  propertyName: string;
  token: string;
  onClose: () => void;
  onManageEquipment: () => void;
}

type FieldErrors = Partial<Record<'hsp' | 'source' | 'sourceDate' | 'offset' | 'pr' | 'autonomy' | 'battery' | 'batteryEfficiency' | 'additionalCosts', string>>;

interface AdditionalCostDraft {
  description: string;
  value: string;
}

const today = () => new Date().toISOString().slice(0, 10);

const PVSimulationForm: React.FC<PVSimulationFormProps> = ({
  propertyId,
  propertyName,
  token,
  onClose,
  onManageEquipment,
}) => {
  const [consumption, setConsumption] = useState<ConsumptionReport | null>(null);
  const [batteries, setBatteries] = useState<PVBatteryCatalogItem[]>([]);
  const [hsp, setHsp] = useState('');
  const [source, setSource] = useState('Entrada manual confirmada pelo usuário');
  const [sourceDate, setSourceDate] = useState(today());
  const [offset, setOffset] = useState('100');
  const [pr, setPr] = useState('80');
  const [withBattery, setWithBattery] = useState(false);
  const [autonomy, setAutonomy] = useState('4');
  const [batteryId, setBatteryId] = useState('');
  const [batteryEfficiency, setBatteryEfficiency] = useState('95');
  const [additionalCosts, setAdditionalCosts] = useState<AdditionalCostDraft[]>([]);
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [simulating, setSimulating] = useState(false);
  const [result, setResult] = useState<PVSimulation | null>(null);
  const [lastRequest, setLastRequest] = useState<PVSimulationRequest | null>(null);
  const [savedProposal, setSavedProposal] = useState<PVProposal | null>(null);
  const [selecting, setSelecting] = useState(false);
  const [saving, setSaving] = useState(false);

  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    let active = true;
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const [reportResponse, solarResponse, batteriesResponse] = await Promise.all([
          api.get<ConsumptionReport>(`/properties/${propertyId}/consumption-report`, { headers }),
          api.get<SolarResource>(`/properties/${propertyId}/solar-resource`, { headers }).catch((requestError) => {
            if (requestError.response?.status === 404) return null;
            throw requestError;
          }),
          api.get<PVBatteryCatalogItem[]>('/api/pv/datasets/batteries', { headers }),
        ]);
        if (!active) return;
        setConsumption(reportResponse.data);
        setBatteries(batteriesResponse.data);
        if (solarResponse) {
          setHsp(solarResponse.data.hsp_kwh_m2_day);
          setSource(solarResponse.data.source);
          setSourceDate(solarResponse.data.source_date);
        }
      } catch {
        if (active) setError('Não foi possível carregar os dados para o dimensionamento. Tente novamente.');
      } finally {
        if (active) setLoading(false);
      }
    };
    void load();
    return () => { active = false; };
    // `headers` is derived only from token; keeping the primitive dependencies avoids reload loops.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [propertyId, token]);

  const validate = () => {
    const errors: FieldErrors = {};
    const numericHsp = Number(hsp);
    const numericOffset = Number(offset);
    const numericPr = Number(pr);
    const numericAutonomy = Number(autonomy);
    const numericEfficiency = Number(batteryEfficiency);
    if (!Number.isFinite(numericHsp) || numericHsp <= 0) errors.hsp = 'Informe um HSP maior que zero.';
    if (!source.trim()) errors.source = 'Informe a origem do HSP.';
    if (!sourceDate) errors.sourceDate = 'Informe a data da origem.';
    if (!Number.isFinite(numericOffset) || numericOffset <= 0 || numericOffset > 100) errors.offset = 'Use um valor maior que 0 e até 100%.';
    if (!Number.isFinite(numericPr) || numericPr <= 0 || numericPr > 100) errors.pr = 'Use um valor maior que 0 e até 100%.';
    if (withBattery) {
      if (!Number.isFinite(numericAutonomy) || numericAutonomy <= 0 || numericAutonomy > 24) errors.autonomy = 'Use uma autonomia maior que 0 e até 24 horas.';
      if (!batteryId) errors.battery = 'Selecione uma bateria.';
      if (!Number.isFinite(numericEfficiency) || numericEfficiency <= 0 || numericEfficiency > 100) errors.batteryEfficiency = 'Use um valor maior que 0 e até 100%.';
    }
    if (additionalCosts.some((item) => {
      const value = Number(item.value);
      return !item.description.trim() || !Number.isFinite(value) || value < 0;
    })) {
      errors.additionalCosts = 'Preencha a descrição e informe um valor igual ou maior que zero para cada custo.';
    }
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setResult(null);
    setError(null);
    if (!validate()) return;

    const payload: PVSimulationRequest = {
      hsp_kwh_m2_day: Number(hsp),
      hsp_source: source.trim(),
      hsp_source_date: sourceDate,
      target_offset_fraction: Number(offset) / 100,
      period_days: 30,
      performance_ratio: Number(pr) / 100,
      autonomy_hours: withBattery ? Number(autonomy) : 0,
      battery_efficiency: Number(batteryEfficiency) / 100,
      additional_costs: additionalCosts.map((item) => ({
        description: item.description.trim(),
        value_brl: Number(item.value),
      })),
      ...(withBattery ? { battery_catalog_id: batteryId } : {}),
    };

    setSimulating(true);
    try {
      const response = await api.post<PVSimulation>(
        `/api/properties/${propertyId}/pv/simulations`,
        payload,
        { headers },
      );
      setResult(response.data);
      setLastRequest(payload);
      setSavedProposal(null);
    } catch (requestError: any) {
      const detail = requestError.response?.data?.detail;
      if (requestError.response?.status === 422 && Array.isArray(detail)) {
        setError(detail.map((item: any) => item.msg).join(' '));
      } else if (detail && typeof detail === 'object' && detail.message) {
        setError(detail.message);
      } else if (typeof detail === 'string') {
        setError(detail);
      } else {
        setError('Não foi possível concluir a simulação. Tente novamente.');
      }
    } finally {
      setSimulating(false);
    }
  };

  const recalculate = async (selection: Partial<PVSimulationRequest>) => {
    if (!lastRequest) return;
    setSelecting(true);
    setError(null);
    setSavedProposal(null);
    const payload: PVSimulationRequest = { ...lastRequest, ...selection };
    if (selection.module_catalog_id) delete payload.inverter_catalog_id;
    try {
      const response = await api.post<PVSimulation>(
        `/api/properties/${propertyId}/pv/simulations`, payload, { headers },
      );
      setResult(response.data);
      setLastRequest(payload);
    } catch (requestError: any) {
      setError(requestError.response?.data?.detail?.message || 'Não foi possível recalcular a solução.');
    } finally {
      setSelecting(false);
    }
  };

  const saveProposal = async () => {
    if (!lastRequest || !result?.budget || !result.selected_inverter) return;
    setSaving(true);
    setError(null);
    try {
      const response = await api.post<PVProposal>(
        `/api/properties/${propertyId}/pv/proposals`, lastRequest, { headers },
      );
      setSavedProposal(response.data);
    } catch (requestError: any) {
      setError(requestError.response?.data?.detail?.message || 'Não foi possível salvar a proposta.');
    } finally {
      setSaving(false);
    }
  };

  const formatNumber = (value: string | number, maximumFractionDigits = 2) =>
    Number(value).toLocaleString('pt-BR', { maximumFractionDigits });
  const formatMoney = (value: string | number) =>
    Number(value).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

  if (loading) {
    return <section className="pv-sizing-section"><button className="secondary-button" onClick={onClose}>← Voltar</button><p className="empty-state" role="status">Carregando consumo e parâmetros solares...</p></section>;
  }

  if (error && !consumption) {
    return <section className="pv-sizing-section"><button className="secondary-button" onClick={onClose}>← Voltar</button><p className="alert" role="alert">{error}</p></section>;
  }

  if (!consumption || consumption.total_monthly_consumption_kwh <= 0 || consumption.items.length === 0) {
    return (
      <section className="pv-sizing-section">
        <button className="secondary-button" onClick={onClose}>← Voltar</button>
        <div className="empty-state">
          <h2>Consumo ainda não disponível</h2>
          <p>Cadastre os equipamentos desta residência antes de dimensionar o sistema solar.</p>
          <button onClick={onManageEquipment}>Gerenciar equipamentos</button>
        </div>
      </section>
    );
  }

  return (
    <section className="pv-sizing-section">
      <button className="secondary-button" onClick={onClose}>← Voltar</button>
      <div className="catalog-header">
        <div><span className="eyebrow">Pré-dimensionamento fotovoltaico</span><h1>Dimensionar sistema solar</h1><p className="subtitle">{propertyName}</p></div>
        <div className="consumption-badge"><span>Consumo calculado</span><strong>{consumption.total_monthly_consumption_kwh.toLocaleString('pt-BR', { maximumFractionDigits: 2 })} kWh/mês</strong><small>Obtido dos equipamentos da residência</small></div>
      </div>

      {!result && <form className="form-card pv-form" onSubmit={submit} noValidate>
        <h3>Parâmetros da simulação</h3>
        <p className="field-help">Confirme o recurso solar e escolha quanto do consumo deseja compensar. O consumo de referência não precisa ser digitado.</p>
        {error && <p className="alert" role="alert">{error}</p>}
        <div className="form-grid">
          <div className="field"><label htmlFor="pv-hsp">HSP (kWh/m²/dia)</label><input id="pv-hsp" type="number" min="0.001" step="0.001" value={hsp} onChange={(event) => setHsp(event.target.value)} aria-invalid={Boolean(fieldErrors.hsp)} aria-describedby={fieldErrors.hsp ? 'pv-hsp-error' : undefined} />{fieldErrors.hsp && <span className="field-error" id="pv-hsp-error">{fieldErrors.hsp}</span>}</div>
          <div className="field"><label htmlFor="pv-source-date">Data da origem</label><input id="pv-source-date" type="date" value={sourceDate} onChange={(event) => setSourceDate(event.target.value)} aria-invalid={Boolean(fieldErrors.sourceDate)} />{fieldErrors.sourceDate && <span className="field-error">{fieldErrors.sourceDate}</span>}</div>
          <div className="field full-width"><label htmlFor="pv-source">Origem do HSP</label><input id="pv-source" maxLength={500} value={source} onChange={(event) => setSource(event.target.value)} aria-invalid={Boolean(fieldErrors.source)} />{fieldErrors.source && <span className="field-error">{fieldErrors.source}</span>}</div>
          <div className="field"><label htmlFor="pv-offset">Compensação desejada (%)</label><input id="pv-offset" type="number" min="0.01" max="100" step="0.01" value={offset} onChange={(event) => setOffset(event.target.value)} aria-invalid={Boolean(fieldErrors.offset)} />{fieldErrors.offset && <span className="field-error">{fieldErrors.offset}</span>}</div>
          <div className="field"><label htmlFor="pv-pr">Performance do sistema — PR (%)</label><input id="pv-pr" type="number" min="0.01" max="100" step="0.01" value={pr} onChange={(event) => setPr(event.target.value)} aria-invalid={Boolean(fieldErrors.pr)} />{fieldErrors.pr && <span className="field-error">{fieldErrors.pr}</span>}</div>
        </div>

        <fieldset className="battery-fieldset">
          <label className="checkbox-field"><input type="checkbox" checked={withBattery} onChange={(event) => setWithBattery(event.target.checked)} />Incluir armazenamento em bateria</label>
          {withBattery && <div className="form-grid battery-fields">
            <div className="field"><label htmlFor="pv-autonomy">Autonomia (horas)</label><input id="pv-autonomy" type="number" min="0.01" max="24" step="0.01" value={autonomy} onChange={(event) => setAutonomy(event.target.value)} aria-invalid={Boolean(fieldErrors.autonomy)} />{fieldErrors.autonomy && <span className="field-error">{fieldErrors.autonomy}</span>}</div>
            <div className="field"><label htmlFor="pv-battery-efficiency">Eficiência da bateria (%)</label><input id="pv-battery-efficiency" type="number" min="0.01" max="100" step="0.01" value={batteryEfficiency} onChange={(event) => setBatteryEfficiency(event.target.value)} aria-invalid={Boolean(fieldErrors.batteryEfficiency)} />{fieldErrors.batteryEfficiency && <span className="field-error">{fieldErrors.batteryEfficiency}</span>}</div>
            <div className="field full-width"><label htmlFor="pv-battery">Modelo de bateria</label><select id="pv-battery" value={batteryId} onChange={(event) => setBatteryId(event.target.value)} aria-invalid={Boolean(fieldErrors.battery)}><option value="">Selecione uma opção</option>{batteries.map((battery) => <option key={battery.id} value={battery.id}>{battery.fabricante} {battery.modelo} — {battery.capacidade_kwh} kWh</option>)}</select>{fieldErrors.battery && <span className="field-error">{fieldErrors.battery}</span>}{batteries.length === 0 && <span className="field-error">Catálogo de baterias vazio.</span>}</div>
          </div>}
        </fieldset>

        <fieldset className="battery-fieldset additional-costs-fieldset">
          <div className="fieldset-heading">
            <div>
              <strong>Custos adicionais</strong>
              <p className="field-help">Inclua somente valores explícitos, como instalação, estrutura, cabeamento ou proteção.</p>
            </div>
            <button
              type="button"
              className="secondary-button"
              onClick={() => setAdditionalCosts((items) => [...items, { description: '', value: '' }])}
              disabled={additionalCosts.length >= 50}
            >
              Adicionar custo
            </button>
          </div>
          {additionalCosts.length === 0 ? (
            <p className="no-storage">Nenhum custo adicional informado.</p>
          ) : (
            <div className="additional-costs-list">
              {additionalCosts.map((item, index) => (
                <div className="additional-cost-row" key={index}>
                  <div className="field">
                    <label htmlFor={`pv-additional-description-${index}`}>Descrição do custo {index + 1}</label>
                    <input
                      id={`pv-additional-description-${index}`}
                      maxLength={300}
                      value={item.description}
                      onChange={(event) => setAdditionalCosts((items) => items.map((current, currentIndex) => (
                        currentIndex === index ? { ...current, description: event.target.value } : current
                      )))}
                    />
                  </div>
                  <div className="field">
                    <label htmlFor={`pv-additional-value-${index}`}>Valor (R$)</label>
                    <input
                      id={`pv-additional-value-${index}`}
                      type="number"
                      min="0"
                      step="0.01"
                      value={item.value}
                      onChange={(event) => setAdditionalCosts((items) => items.map((current, currentIndex) => (
                        currentIndex === index ? { ...current, value: event.target.value } : current
                      )))}
                    />
                  </div>
                  <button
                    type="button"
                    className="danger-button remove-additional-cost"
                    aria-label={`Remover custo ${index + 1}`}
                    onClick={() => setAdditionalCosts((items) => items.filter((_, currentIndex) => currentIndex !== index))}
                  >
                    Remover
                  </button>
                </div>
              ))}
            </div>
          )}
          {fieldErrors.additionalCosts && <span className="field-error">{fieldErrors.additionalCosts}</span>}
        </fieldset>

        <div className="form-actions"><button type="button" className="secondary-button" onClick={onClose}>Cancelar</button><button type="submit" disabled={simulating}>{simulating ? 'Calculando solução...' : 'Simular sistema'}</button></div>
      </form>}

      {result && (
        <div className="pv-results" aria-live="polite">
          <div className="pv-results-heading">
            <div><span className="eyebrow">Simulação concluída</span><h2>Resumo técnico da solução</h2></div>
            <button type="button" className="secondary-button" onClick={() => { setResult(null); setSavedProposal(null); }}>← Voltar e recalcular</button>
          </div>
          {error && <p className="alert" role="alert">{error}</p>}

          <div className="pv-metrics">
            <div><span>Consumo de referência</span><strong>{formatNumber(result.calculation.reference_consumption.value)} {result.calculation.reference_consumption.unit}</strong></div>
            <div><span>Geração estimada</span><strong>{formatNumber(result.calculation.target_energy.value)} {result.calculation.target_energy.unit}</strong></div>
            <div><span>Potência necessária</span><strong>{formatNumber(result.calculation.required_pv_power.value)} {result.calculation.required_pv_power.unit}</strong></div>
            <div><span>Potência instalada</span><strong>{formatNumber(result.selected_module.installed_power_kwp)} kWp</strong></div>
          </div>

          <section className="pv-result-section">
            <h3>1. Escolha dos módulos</h3>
            <div className="pv-option-grid">
              {result.module_alternatives.map((module) => {
                const selected = module.catalog_id === result.selected_module.catalog_id;
                return <article className={`pv-component-card ${selected ? 'selected' : ''}`} key={module.catalog_id}>
                  <span className="component-kind">Módulo fotovoltaico</span>
                  <h4>{module.manufacturer} {module.model}</h4>
                  <p>{module.module_quantity} módulos × {formatNumber(module.module_power_wp, 0)} Wp</p>
                  <p><strong>{formatNumber(module.installed_power_kwp)} kWp</strong> instalados</p>
                  <p>{formatMoney(module.total_price_brl)}</p>
                  <button type="button" className={selected ? 'secondary-button' : ''} disabled={selected || selecting} onClick={() => void recalculate({ module_catalog_id: module.catalog_id })}>{selected ? 'Selecionado' : 'Selecionar módulo'}</button>
                </article>;
              })}
            </div>
          </section>

          <section className="pv-result-section">
            <h3>2. Escolha do inversor e strings</h3>
            <div className="pv-option-grid">
              {result.compatible_inverters.map((inverter) => {
                const selected = inverter.catalog_id === result.selected_inverter?.catalog_id;
                return <article className={`pv-component-card ${selected ? 'selected' : ''}`} key={inverter.catalog_id}>
                  <span className="component-kind">Inversor {inverter.inverter_type}</span>
                  <h4>{inverter.manufacturer} {inverter.model}</h4>
                  <p>{inverter.battery_compatible ? 'Compatível com bateria' : 'Uso on-grid'}</p>
                  <ul className="string-list">{inverter.arrangement.map((string) => <li key={string.mppt_id}>MPPT {string.mppt_id}: {string.module_quantity} módulos · Voc {formatNumber(string.voc_v)} V · Vmp {formatNumber(string.vmp_v)} V</li>)}</ul>
                  <p><strong>{formatMoney(inverter.unit_price_brl)}</strong></p>
                  <button type="button" className={selected ? 'secondary-button' : ''} disabled={selected || selecting} onClick={() => void recalculate({ inverter_catalog_id: inverter.catalog_id })}>{selected ? 'Selecionado' : 'Selecionar inversor'}</button>
                </article>;
              })}
            </div>
          </section>

          <section className="pv-result-section storage-summary">
            <h3>3. Armazenamento</h3>
            {result.storage.storage_requested ? <div className="pv-metrics">
              <div><span>Autonomia</span><strong>{formatNumber(result.storage.autonomy.value)} {result.storage.autonomy.unit}</strong></div>
              <div><span>Capacidade requerida</span><strong>{formatNumber(result.storage.required_nominal_capacity.value)} {result.storage.required_nominal_capacity.unit}</strong></div>
              <div><span>Baterias</span><strong>{result.storage.battery_quantity} unidade(s)</strong></div>
              <div><span>Capacidade instalada</span><strong>{formatNumber(result.storage.installed_nominal_capacity.value)} {result.storage.installed_nominal_capacity.unit}</strong></div>
            </div> : <p className="no-storage">Sistema sem armazenamento: autonomia, capacidade e custo de baterias iguais a zero.</p>}
          </section>

          {result.budget ? <section className="pv-result-section budget-section">
            <h3>4. Orçamento e BOM</h3>
            <div className="bom-table-wrap"><table className="bom-table"><thead><tr><th>Item</th><th>Qtd.</th><th>Preço unitário</th><th>Subtotal</th></tr></thead><tbody>{result.budget.items.map((item, index) => <tr key={`${item.category}-${item.catalog_id || index}`}><td>{item.description}<small>{item.supplier ? `Fornecedor: ${item.supplier}` : item.category === 'additional' ? 'Custo adicional' : ''}</small></td><td>{item.quantity} {item.unit}</td><td>{formatMoney(item.unit_price_brl)}</td><td>{formatMoney(item.subtotal_brl)}</td></tr>)}</tbody></table></div>
            <div className="budget-total"><span>Total preliminar</span><strong>{formatMoney(result.budget.total_cost_brl)}</strong></div>
            {savedProposal ? <p className="success-message" role="status">Proposta #{savedProposal.id} salva com sucesso. Os valores e dados técnicos foram preservados.</p> : <button type="button" className="save-proposal-button" disabled={saving} onClick={() => void saveProposal()}>{saving ? 'Salvando proposta...' : 'Salvar proposta preliminar'}</button>}
          </section> : <p className="selection-guidance">Selecione um inversor compatível para gerar a BOM e habilitar o salvamento da proposta.</p>}

          <aside className="academic-disclaimer"><strong>Aviso acadêmico permanente</strong><p>{result.disclaimer}</p><small>Metodologia: {result.methodology_version}</small></aside>
        </div>
      )}
    </section>
  );
};

export default PVSimulationForm;
