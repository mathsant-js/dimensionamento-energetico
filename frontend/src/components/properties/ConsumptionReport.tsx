import React, { useState, useEffect } from 'react';
import api from '../../api.ts';
import { ConsumptionReport } from '../../types/equipment.ts';
import './ConsumptionReport.css';

interface ConsumptionReportProps {
  propertyId: number;
  propertyName: string;
  onClose: () => void;
  token: string;
}

const ConsumptionReportComponent: React.FC<ConsumptionReportProps> = ({
  propertyId,
  propertyName,
  onClose,
  token,
}) => {
  const [report, setReport] = useState<ConsumptionReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchReport = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await api.get<ConsumptionReport>(
          `/properties/${propertyId}/consumption-report`,
          {
            headers: { Authorization: `Bearer ${token}` },
          }
        );
        setReport(response.data);
      } catch (err: any) {
        setError('Não foi possível carregar o relatório de consumo.');
      } finally {
        setLoading(false);
      }
    };

    fetchReport();
  }, [propertyId, token]);

  if (loading) {
    return (
      <div className="consumption-report-container">
        <div className="consumption-report-header">
          <h2>Carregando relatório...</h2>
          <button className="close-button" onClick={onClose}>✕</button>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="consumption-report-container">
        <div className="consumption-report-header">
          <h2>Relatório de Consumo</h2>
          <button className="close-button" onClick={onClose}>✕</button>
        </div>
        <div className="alert">{error}</div>
        <button className="secondary-button" onClick={onClose}>Voltar</button>
      </div>
    );
  }

  if (!report || report.items.length === 0) {
    return (
      <div className="consumption-report-container">
        <div className="consumption-report-header">
          <h2>Relatório de Consumo - {propertyName}</h2>
          <button className="close-button" onClick={onClose}>✕</button>
        </div>
        <div className="empty-state">
          <p>Nenhum equipamento cadastrado para esta propriedade ainda.</p>
          <p className="subtitle">Adicione equipamentos para gerar o relatório de consumo.</p>
        </div>
        <button className="secondary-button" onClick={onClose}>Voltar</button>
      </div>
    );
  }

  return (
    <div className="consumption-report-container">
      <div className="consumption-report-header">
        <div>
          <h2>Relatório de Consumo - {propertyName}</h2>
          <p className="report-subtitle">{report.property_type}</p>
        </div>
        <button className="close-button" onClick={onClose}>✕</button>
      </div>

      <div className="report-content">
        <section className="equipments-section">
          <h3>Equipamentos Cadastrados</h3>
          <div className="table-wrapper">
            <table className="equipments-table">
              <thead>
                <tr>
                  <th>Equipamento</th>
                  <th>Potência (W)</th>
                  <th>Quantidade</th>
                  <th>Horas/dia</th>
                  <th>Consumo Mensal (kWh)</th>
                </tr>
              </thead>
              <tbody>
                {report.items.map((item) => (
                  <tr key={item.id}>
                    <td className="equipment-name">{item.equipment_name}</td>
                    <td className="numeric">{item.power_watts.toFixed(0)}</td>
                    <td className="numeric">{item.quantity}</td>
                    <td className="numeric">{item.hours_per_day.toFixed(1)}</td>
                    <td className="numeric consumption">
                      {item.monthly_consumption_kwh.toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="summary-section">
          <div className="summary-card">
            <div className="summary-item">
              <span className="summary-label">Total de Equipamentos</span>
              <span className="summary-value">{report.items.length}</span>
            </div>
            <div className="summary-item total">
              <span className="summary-label">Consumo Total Mensal</span>
              <span className="summary-value total-value">
                {report.total_monthly_consumption_kwh.toFixed(2)} kWh
              </span>
            </div>
          </div>
        </section>

        <section className="actions-section">
          <button className="secondary-button" onClick={onClose}>Voltar</button>
        </section>
      </div>
    </div>
  );
};

export default ConsumptionReportComponent;
