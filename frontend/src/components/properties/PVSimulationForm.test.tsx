import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import api from '../../api.ts';
import PVSimulationForm from './PVSimulationForm.tsx';

jest.mock('../../api.ts', () => ({
  __esModule: true,
  default: { get: jest.fn(), post: jest.fn() },
}));

const mockedApi = api as jest.Mocked<typeof api>;

const report = {
  property_id: 7,
  property_name: 'Casa Solar',
  property_type: 'casa',
  total_monthly_consumption_kwh: 420.5,
  created_at: '2026-10-09T12:00:00Z',
  items: [{
    id: 1,
    equipment_name: 'Geladeira',
    power_watts: 200,
    quantity: 1,
    hours_per_day: 24,
    monthly_consumption_kwh: 144,
  }],
};

const solarResource = {
  id: 1,
  property_id: 7,
  hsp_kwh_m2_day: '5.1',
  unit: 'kWh/m²/dia',
  source: 'Atlas Solar',
  source_date: '2026-10-01',
  acquisition_mode: 'manual',
  created_at: '2026-10-09T12:00:00Z',
  updated_at: '2026-10-09T12:00:00Z',
};

const simulation = {
  property_id: 7,
  consumption_calculated_at: '2026-10-09T12:00:00Z',
  calculation: {
    reference_consumption: { value: '420.5', unit: 'kWh/mês' },
    target_offset: { value: '80', unit: '%' },
    hsp: { value: '5.1', unit: 'kWh/m²/dia' },
    period_days: { value: '30', unit: 'dias' },
    performance_ratio: { value: '80', unit: '%' },
    target_energy: { value: '336.4', unit: 'kWh/mês' },
    required_pv_power: { value: '2.75', unit: 'kWp' },
  },
  module_alternatives: [{ catalog_id: 'MOD-1', manufacturer: 'Solar', model: 'M550', module_power_wp: '550', module_quantity: 5, installed_power_kwp: '2.75', unit_price_brl: '700', total_price_brl: '3500' }],
  selected_module: { catalog_id: 'MOD-1', manufacturer: 'Solar', model: 'M550', module_power_wp: '550', module_quantity: 5, installed_power_kwp: '2.75', unit_price_brl: '700', total_price_brl: '3500' },
  compatible_inverters: [{ catalog_id: 'INV-1', manufacturer: 'Volt', model: 'I3000', inverter_type: 'on-grid', battery_compatible: false, unit_price_brl: '2500', installed_pv_power_w: '2750', arrangement: [{ mppt_id: 1, module_quantity: 5, voc_v: '250', vmp_v: '210' }] }],
  rejected_inverters: [],
  selected_inverter: null,
  storage: { storage_requested: false, daily_consumption: { value: '14.02', unit: 'kWh/dia' }, autonomy: { value: '0', unit: 'h' }, autonomy_energy: { value: '0', unit: 'kWh' }, battery_efficiency: { value: '95', unit: '%' }, battery_catalog_id: null, depth_of_discharge: { value: '0', unit: '%' }, required_nominal_capacity: { value: '0', unit: 'kWh' }, battery_quantity: 0, installed_nominal_capacity: { value: '0', unit: 'kWh' }, installed_deliverable_energy: { value: '0', unit: 'kWh' }, total_battery_cost: { value: '0', unit: 'BRL' } },
  budget: null,
  methodology_version: 'ADR-001/v1',
  disclaimer: 'Pré-dimensionamento acadêmico; não substitui projeto executivo.',
};

const renderForm = () => render(
  <PVSimulationForm
    propertyId={7}
    propertyName="Casa Solar"
    token="token"
    onClose={jest.fn()}
    onManageEquipment={jest.fn()}
  />,
);

beforeEach(() => {
  jest.clearAllMocks();
  mockedApi.get.mockImplementation((url: string) => {
    if (url.includes('consumption-report')) return Promise.resolve({ data: report });
    if (url.includes('solar-resource')) return Promise.resolve({ data: solarResource });
    if (url.includes('batteries')) return Promise.resolve({ data: [] });
    return Promise.reject(new Error('unexpected request'));
  });
});

test('uses the property consumption without asking the user to type it again', async () => {
  renderForm();

  expect(await screen.findByText('420,5 kWh/mês')).toBeInTheDocument();
  expect(screen.getByText(/obtido dos equipamentos da residência/i)).toBeInTheDocument();
  expect(screen.queryByLabelText(/consumo/i)).not.toBeInTheDocument();
  expect(screen.getByLabelText(/^HSP \(/i)).toHaveValue(5.1);
  expect(screen.getByLabelText(/^origem do HSP$/i)).toHaveValue('Atlas Solar');
});

test('validates fields and sends percentages as fractions to the simulation API', async () => {
  mockedApi.post.mockResolvedValue({
    data: simulation,
  });
  renderForm();
  await screen.findByText('420,5 kWh/mês');

  fireEvent.change(screen.getByLabelText(/compensação desejada/i), { target: { value: '0' } });
  fireEvent.click(screen.getByRole('button', { name: /simular sistema/i }));
  expect(await screen.findByText(/maior que 0 e até 100%/i)).toBeInTheDocument();
  expect(mockedApi.post).not.toHaveBeenCalled();

  fireEvent.change(screen.getByLabelText(/compensação desejada/i), { target: { value: '80' } });
  fireEvent.click(screen.getByRole('button', { name: /simular sistema/i }));

  await waitFor(() => expect(mockedApi.post).toHaveBeenCalledTimes(1));
  expect(mockedApi.post).toHaveBeenCalledWith(
    '/api/properties/7/pv/simulations',
    expect.objectContaining({
      target_offset_fraction: 0.8,
      performance_ratio: 0.8,
      autonomy_hours: 0,
    }),
    expect.objectContaining({ headers: { Authorization: 'Bearer token' } }),
  );
  expect(await screen.findByText(/resumo técnico da solução/i)).toBeInTheDocument();
  expect(screen.getAllByText(/2,75 kWp/i).length).toBeGreaterThanOrEqual(2);
  expect(screen.getByText(/sistema sem armazenamento/i)).toBeInTheDocument();
  expect(screen.getByText(/aviso acadêmico permanente/i)).toBeInTheDocument();
});

test('validates and sends explicit additional costs to the simulation API', async () => {
  mockedApi.post.mockResolvedValue({ data: simulation });
  renderForm();
  await screen.findByText('420,5 kWh/mês');

  fireEvent.click(screen.getByRole('button', { name: /adicionar custo/i }));
  fireEvent.click(screen.getByRole('button', { name: /simular sistema/i }));
  expect(await screen.findByText(/preencha a descrição/i)).toBeInTheDocument();
  expect(mockedApi.post).not.toHaveBeenCalled();

  fireEvent.change(screen.getByLabelText(/descrição do custo 1/i), { target: { value: 'Instalação' } });
  fireEvent.change(screen.getByLabelText(/^valor \(R\$\)$/i), { target: { value: '1500.00' } });
  fireEvent.click(screen.getByRole('button', { name: /simular sistema/i }));

  await waitFor(() => expect(mockedApi.post).toHaveBeenCalledTimes(1));
  expect(mockedApi.post).toHaveBeenCalledWith(
    '/api/properties/7/pv/simulations',
    expect.objectContaining({
      additional_costs: [{ description: 'Instalação', value_brl: 1500 }],
    }),
    expect.any(Object),
  );
});

test('selects an inverter, renders the BOM and persists the proposal', async () => {
  const withBudget = {
    ...simulation,
    selected_inverter: simulation.compatible_inverters[0],
    budget: {
      currency: 'BRL',
      items: [
        { category: 'module', description: 'Módulo Solar M550', quantity: 5, unit: 'unidade', unit_price_brl: '700', subtotal_brl: '3500', catalog_id: 'MOD-1', manufacturer: 'Solar', model: 'M550', supplier: 'Loja Solar', source_url: 'https://example.test/module' },
        { category: 'inverter', description: 'Inversor Volt I3000', quantity: 1, unit: 'unidade', unit_price_brl: '2500', subtotal_brl: '2500', catalog_id: 'INV-1', manufacturer: 'Volt', model: 'I3000', supplier: 'Loja Solar', source_url: 'https://example.test/inverter' },
      ],
      modules_cost_brl: '3500', inverter_cost_brl: '2500', batteries_cost_brl: '0', additional_cost_brl: '0', equipment_cost_brl: '6000', total_cost_brl: '6000',
    },
  };
  mockedApi.post
    .mockResolvedValueOnce({ data: simulation })
    .mockResolvedValueOnce({ data: withBudget })
    .mockResolvedValueOnce({ data: { id: 31, property_id: 7, total_cost_brl: '6000', created_at: '2026-10-10T12:00:00Z' } });
  renderForm();
  await screen.findByText('420,5 kWh/mês');
  fireEvent.click(screen.getByRole('button', { name: /simular sistema/i }));
  fireEvent.click(await screen.findByRole('button', { name: /selecionar inversor/i }));

  expect(await screen.findByText('Módulo Solar M550')).toBeInTheDocument();
  expect(screen.getByText('R$ 6.000,00')).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: /salvar proposta preliminar/i }));
  expect(await screen.findByText(/proposta #31 salva com sucesso/i)).toBeInTheDocument();
  expect(mockedApi.post).toHaveBeenLastCalledWith(
    '/api/properties/7/pv/proposals',
    expect.objectContaining({ inverter_catalog_id: 'INV-1' }),
    expect.any(Object),
  );
});

test('renders storage units and battery costs in the battery scenario', async () => {
  mockedApi.get.mockImplementation((url: string) => {
    if (url.includes('consumption-report')) return Promise.resolve({ data: report });
    if (url.includes('solar-resource')) return Promise.resolve({ data: solarResource });
    if (url.includes('batteries')) return Promise.resolve({ data: [{ id: 'BAT-1', fabricante: 'Lítio', modelo: 'B5', capacidade_kwh: '5', dod_pct: '90', preco_brl: '9000' }] });
    return Promise.reject(new Error('unexpected request'));
  });
  mockedApi.post.mockResolvedValue({
    data: {
      ...simulation,
      storage: {
        ...simulation.storage,
        storage_requested: true,
        autonomy: { value: '4', unit: 'h' },
        required_nominal_capacity: { value: '2.46', unit: 'kWh' },
        battery_quantity: 1,
        installed_nominal_capacity: { value: '5', unit: 'kWh' },
        total_battery_cost: { value: '9000', unit: 'BRL' },
      },
    },
  });
  renderForm();
  await screen.findByText('420,5 kWh/mês');
  fireEvent.click(screen.getByLabelText(/incluir armazenamento/i));
  fireEvent.change(screen.getByLabelText(/modelo de bateria/i), { target: { value: 'BAT-1' } });
  fireEvent.click(screen.getByRole('button', { name: /simular sistema/i }));

  expect(await screen.findByText('4 h')).toBeInTheDocument();
  expect(screen.getByText('2,46 kWh')).toBeInTheDocument();
  expect(screen.getByText('1 unidade(s)')).toBeInTheDocument();
  expect(screen.queryByText(/sistema sem armazenamento/i)).not.toBeInTheDocument();
});

test('shows an empty state when the property has no calculated consumption', async () => {
  mockedApi.get.mockImplementation((url: string) => {
    if (url.includes('consumption-report')) return Promise.resolve({ data: { ...report, items: [], total_monthly_consumption_kwh: 0 } });
    if (url.includes('solar-resource')) return Promise.reject({ response: { status: 404 } });
    return Promise.resolve({ data: [] });
  });
  renderForm();

  expect(await screen.findByText(/consumo ainda não disponível/i)).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /gerenciar equipamentos/i })).toBeInTheDocument();
});
