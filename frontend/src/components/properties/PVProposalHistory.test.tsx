import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import api from '../../api.ts';
import PVProposalHistory from './PVProposalHistory.tsx';

jest.mock('../../api.ts', () => ({
  __esModule: true,
  default: { get: jest.fn(), delete: jest.fn() },
}));

const mockedApi = api as jest.Mocked<typeof api>;
const proposal: any = {
  id: 31, property_id: 7, status: 'draft', created_at: '2026-10-10T12:00:00Z', updated_at: '2026-10-10T12:00:00Z',
  reference_consumption_kwh_month: '300', hsp_kwh_m2_day: '5', hsp_source: 'Atlas', hsp_source_date: '2026-10-10',
  target_offset_fraction: '1', performance_ratio: '0.8', target_energy_kwh: '300', required_pv_power_kwp: '2.5', installed_pv_power_kwp: '2.75',
  battery_requested: false, autonomy_hours: '0', required_battery_capacity_kwh: '0', installed_battery_capacity_kwh: '0',
  modules_cost_brl: '2945', inverter_cost_brl: '2899', batteries_cost_brl: '0', additional_cost_brl: '0', equipment_cost_brl: '5844', total_cost_brl: '5844',
  methodology_version: 'ADR-001/v1', disclaimer: 'Pré-dimensionamento acadêmico.',
  items: [{ id: 1, item_type: 'module', description: 'Módulo 550 Wp', quantity: '5', unit: 'unidade', unit_price_brl: '589', subtotal_brl: '2945', supplier: 'Fornecedor', string_configuration: [{ mppt_id: 1, module_quantity: 5, voc_v: '248', vmp_v: '208.5' }] }],
};

beforeEach(() => jest.clearAllMocks());

test('lists and reopens a persisted proposal with its snapshot', async () => {
  mockedApi.get.mockResolvedValue({ data: [proposal] });
  render(<PVProposalHistory propertyId={7} propertyName="Casa Solar" token="token" onClose={jest.fn()} />);
  expect(await screen.findByText('Proposta #31')).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: /consultar/i }));
  expect(screen.getByText(/proposta fotovoltaica salva/i)).toBeInTheDocument();
  expect(screen.getByText('Módulo 550 Wp')).toBeInTheDocument();
  expect(screen.getByText('R$ 5.844,00')).toBeInTheDocument();
  expect(screen.getByText(/MPPT 1: 5 módulos/i)).toBeInTheDocument();
});

test('deletes a proposal and removes it from the history', async () => {
  mockedApi.get.mockResolvedValue({ data: [proposal] });
  mockedApi.delete.mockResolvedValue({});
  render(<PVProposalHistory propertyId={7} propertyName="Casa Solar" token="token" onClose={jest.fn()} />);
  fireEvent.click(await screen.findByRole('button', { name: /excluir/i }));
  await waitFor(() => expect(mockedApi.delete).toHaveBeenCalledWith(
    '/api/properties/7/pv/proposals/31',
    expect.objectContaining({ headers: { Authorization: 'Bearer token' } }),
  ));
  expect(await screen.findByText(/nenhuma proposta salva/i)).toBeInTheDocument();
});
