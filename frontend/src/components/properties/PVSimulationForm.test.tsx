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
    data: {
      property_id: 7,
      calculation: {
        reference_consumption: { value: '420.5', unit: 'kWh/mês' },
        target_energy: { value: '336.4', unit: 'kWh/mês' },
        required_pv_power: { value: '2.75', unit: 'kWp' },
      },
      module_alternatives: [{}],
      compatible_inverters: [{}],
      selected_inverter: {},
      budget: {},
      disclaimer: 'Preliminar',
    },
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
  expect(await screen.findByText(/2.75 kWp necessários/i)).toBeInTheDocument();
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
