export interface PVBatteryCatalogItem {
  id: string;
  fabricante: string;
  modelo: string;
  capacidade_kwh: string;
  dod_pct: string;
  preco_brl: string;
}

export interface PVSimulationRequest {
  hsp_kwh_m2_day: number;
  hsp_source: string;
  hsp_source_date: string;
  target_offset_fraction: number;
  period_days: number;
  performance_ratio: number;
  autonomy_hours: number;
  battery_efficiency: number;
  battery_catalog_id?: string;
  additional_costs: [];
}

export interface PVQuantity {
  value: string;
  unit: string;
}

export interface PVSimulation {
  property_id: number;
  calculation: {
    reference_consumption: PVQuantity;
    target_energy: PVQuantity;
    required_pv_power: PVQuantity;
  };
  module_alternatives: unknown[];
  compatible_inverters: unknown[];
  selected_inverter: unknown | null;
  budget: unknown | null;
  disclaimer: string;
}
