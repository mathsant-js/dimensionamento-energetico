import React, { useEffect, useState } from 'react';
import api from '../../api.ts';
import { PVProposal } from '../../types/pv.ts';

interface Props {
  propertyId: number;
  propertyName: string;
  token: string;
  onClose: () => void;
}

const money = (value: string | number) => Number(value).toLocaleString('pt-BR', {
  style: 'currency', currency: 'BRL',
});
const number = (value: string | number, digits = 2) => Number(value).toLocaleString('pt-BR', {
  maximumFractionDigits: digits,
});

const PVProposalHistory: React.FC<Props> = ({ propertyId, propertyName, token, onClose }) => {
  const [proposals, setProposals] = useState<PVProposal[]>([]);
  const [selected, setSelected] = useState<PVProposal | null>(null);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    let active = true;
    api.get<PVProposal[]>(`/api/properties/${propertyId}/pv/proposals`, { headers })
      .then((response) => { if (active) setProposals(response.data); })
      .catch(() => { if (active) setError('Não foi possível carregar as propostas.'); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [propertyId, token]);

  const remove = async (proposalId: number) => {
    setDeleting(proposalId);
    setError(null);
    try {
      await api.delete(`/api/properties/${propertyId}/pv/proposals/${proposalId}`, { headers });
      setProposals((current) => current.filter((proposal) => proposal.id !== proposalId));
      if (selected?.id === proposalId) setSelected(null);
    } catch {
      setError('Não foi possível excluir a proposta.');
    } finally {
      setDeleting(null);
    }
  };

  if (selected) {
    return <section className="pv-sizing-section">
      <button className="secondary-button" onClick={() => setSelected(null)}>← Voltar ao histórico</button>
      <div className="catalog-header"><div><span className="eyebrow">Proposta #{selected.id}</span><h1>Proposta fotovoltaica salva</h1><p className="subtitle">{propertyName} · {new Date(selected.created_at).toLocaleString('pt-BR')}</p></div></div>
      <div className="saved-proposal-content">
        <div className="pv-metrics">
          <div><span>Consumo de referência</span><strong>{number(selected.reference_consumption_kwh_month)} kWh/mês</strong></div>
          <div><span>Energia-alvo</span><strong>{number(selected.target_energy_kwh)} kWh/mês</strong></div>
          <div><span>Potência necessária</span><strong>{number(selected.required_pv_power_kwp)} kWp</strong></div>
          <div><span>Potência instalada</span><strong>{number(selected.installed_pv_power_kwp)} kWp</strong></div>
        </div>
        <section className="pv-result-section budget-section">
          <h3>Componentes e custos preservados</h3>
          <div className="bom-table-wrap"><table className="bom-table"><thead><tr><th>Item</th><th>Qtd.</th><th>Preço unitário</th><th>Subtotal</th></tr></thead><tbody>
            {selected.items.map((item) => <tr key={item.id}><td>{item.description}<small>{item.supplier ? `Fornecedor: ${item.supplier}` : ''}</small></td><td>{number(item.quantity)} {item.unit}</td><td>{money(item.unit_price_brl)}</td><td>{money(item.subtotal_brl)}</td></tr>)}
          </tbody></table></div>
          <div className="budget-total"><span>Total preliminar</span><strong>{money(selected.total_cost_brl)}</strong></div>
        </section>
        {selected.items.flatMap((item) => item.string_configuration || []).length > 0 && <section className="pv-result-section"><h3>Configuração de strings</h3><ul className="string-list">{selected.items.flatMap((item) => item.string_configuration || []).map((string) => <li key={string.mppt_id}>MPPT {string.mppt_id}: {string.module_quantity} módulos · Voc {number(string.voc_v)} V · Vmp {number(string.vmp_v)} V</li>)}</ul></section>}
        <aside className="academic-disclaimer"><strong>Aviso acadêmico permanente</strong><p>{selected.disclaimer}</p><small>Metodologia: {selected.methodology_version}</small></aside>
      </div>
    </section>;
  }

  return <section className="pv-sizing-section">
    <button className="secondary-button" onClick={onClose}>← Voltar</button>
    <div className="catalog-header"><div><span className="eyebrow">Histórico fotovoltaico</span><h1>Propostas salvas</h1><p className="subtitle">{propertyName}</p></div></div>
    {error && <p className="alert" role="alert">{error}</p>}
    {loading ? <p className="empty-state" role="status">Carregando propostas...</p> : proposals.length === 0 ? <p className="empty-state">Nenhuma proposta salva para esta residência.</p> : <div className="pv-option-grid">{proposals.map((proposal) => <article className="pv-component-card" key={proposal.id}>
      <span className="component-kind">Proposta #{proposal.id}</span>
      <h3>{money(proposal.total_cost_brl)}</h3>
      <p>{number(proposal.installed_pv_power_kwp)} kWp · {proposal.battery_requested ? `${number(proposal.autonomy_hours)} h de autonomia` : 'Sem bateria'}</p>
      <p>{new Date(proposal.created_at).toLocaleString('pt-BR')}</p>
      <div className="card-actions"><button onClick={() => setSelected(proposal)}>Consultar</button><button className="danger-button" disabled={deleting === proposal.id} onClick={() => void remove(proposal.id)}>{deleting === proposal.id ? 'Excluindo...' : 'Excluir'}</button></div>
    </article>)}</div>}
  </section>;
};

export default PVProposalHistory;
