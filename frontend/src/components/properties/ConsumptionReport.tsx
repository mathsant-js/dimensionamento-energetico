import React, { useState, useEffect } from 'react';
import api from '../../api.ts';
import { ConsumptionReport } from '../../types/equipment.ts';
import ConsumptionChart from './ConsumptionChart.tsx';
import './ConsumptionReport.css';

interface ConsumptionReportProps {
  propertyId: number;
  propertyName: string;
  onClose: () => void;
  onManageEquipment: () => void;
  token: string;
}

const formatMonthlyConsumption = (value: number) => (
  `${value.toLocaleString('pt-BR', { maximumFractionDigits: 2 })} kWh/mês`
);

const ConsumptionReportComponent: React.FC<ConsumptionReportProps> = ({
  propertyId,
  propertyName,
  onClose,
  onManageEquipment,
  token,
}) => {
  const [report, setReport] = useState<ConsumptionReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [chartType, setChartType] = useState<'pie' | 'bar'>('pie');

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
          <button onClick={onManageEquipment}>Adicionar primeiro equipamento</button>
        </div>
        <section className="actions-section"><button className="secondary-button" onClick={onClose}>Voltar</button></section>
      </div>
    );
  }

  // Find equipment with highest consumption
  const highestConsumer = report.items.reduce((max, item) => 
    item.monthly_consumption_kwh > max.monthly_consumption_kwh ? item : max
  );

  // Sort items by consumption (highest first)
  const sortedItems = [...report.items].sort((a, b) => 
    b.monthly_consumption_kwh - a.monthly_consumption_kwh
  );

  // Calculate percentage of total for each item
  const itemsWithPercentage = sortedItems.map(item => ({
    ...item,
    percentage: (item.monthly_consumption_kwh / report.total_monthly_consumption_kwh) * 100
  }));

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
        {/* Highest Consumer Alert */}
        <section className="highest-consumer-section">
          <div className="highest-consumer-card">
            <div className="highest-consumer-icon">⚡</div>
            <div className="highest-consumer-content">
              <h3>Maior Consumidor</h3>
              <p className="highest-consumer-name">{highestConsumer.equipment_name}</p>
              <p className="highest-consumer-value">
                {formatMonthlyConsumption(highestConsumer.monthly_consumption_kwh)}
                <span className="highest-consumer-percentage">
                  ({((highestConsumer.monthly_consumption_kwh / report.total_monthly_consumption_kwh) * 100).toFixed(1)}% do total)
                </span>
              </p>
            </div>
          </div>
        </section>

        {/* Consumption Chart Section */}
        <section className="chart-section">
          <div className="chart-header">
            <h3>Participação Percentual do Consumo</h3>
            <div className="chart-type-toggle">
              <button
                className={`toggle-button ${chartType === 'pie' ? 'active' : ''}`}
                onClick={() => setChartType('pie')}
              >
                📊 Pizza
              </button>
              <button
                className={`toggle-button ${chartType === 'bar' ? 'active' : ''}`}
                onClick={() => setChartType('bar')}
              >
                📈 Barras
              </button>
            </div>
          </div>
          <ConsumptionChart
            items={report.items}
            total={report.total_monthly_consumption_kwh}
            chartType={chartType}
          />
        </section>
        <section className="equipments-section">
          <h3>Comparação de Consumo por Equipamento</h3>
          <div className="table-wrapper">
            <table className="equipments-table">
              <thead>
                <tr>
                  <th>Equipamento</th>
                  <th>Potência (W)</th>
                  <th>Quantidade</th>
                  <th>Horas/dia</th>
                  <th>Consumo mensal</th>
                  <th>% do Total</th>
                </tr>
              </thead>
              <tbody>
                {itemsWithPercentage.map((item) => (
                  <tr key={item.id} className={item.id === highestConsumer.id ? 'highest-row' : ''}>
                    <td className="equipment-name">
                      {item.id === highestConsumer.id && <span className="highest-badge">⚡</span>}
                      {item.equipment_name}
                    </td>
                    <td className="numeric">{item.power_watts.toFixed(0)}</td>
                    <td className="numeric">{item.quantity}</td>
                    <td className="numeric">{item.hours_per_day.toFixed(1)}</td>
                    <td className="numeric consumption">
                      <span>{formatMonthlyConsumption(item.monthly_consumption_kwh)}</span>
                      <small>{item.power_watts} W × {item.quantity} × {item.hours_per_day} h/dia × 30 ÷ 1000</small>
                    </td>
                    <td className="numeric percentage">
                      <div className="percentage-bar-container">
                        <div 
                          className="percentage-bar" 
                          style={{ 
                            width: `${item.percentage}%`,
                            backgroundColor: item.id === highestConsumer.id ? '#dc2626' : '#3b82f6'
                          }}
                        ></div>
                        <span className="percentage-text">{item.percentage.toFixed(1)}%</span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* Summary Section */}
        <section className="summary-section">
          <div className="summary-card">
            <div className="summary-item">
              <span className="summary-label">Total de Equipamentos</span>
              <span className="summary-value">{report.items.length}</span>
            </div>
            <div className="summary-item">
              <span className="summary-label">Equipamento com Maior Consumo</span>
              <span className="summary-value summary-equipment">{highestConsumer.equipment_name}</span>
            </div>
            <div className="summary-item total">
              <span className="summary-label">Consumo Total Mensal</span>
              <span className="summary-value total-value">
                {formatMonthlyConsumption(report.total_monthly_consumption_kwh)}
              </span>
            </div>
          </div>
        </section>

        <section className="actions-section">
          <button className="secondary-button" onClick={onClose}>Voltar</button>
          <button onClick={onManageEquipment}>Gerenciar equipamentos</button>
        </section>
      </div>
    </div>
  );
};

export default ConsumptionReportComponent;
