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
  module_catalog_id?: string;
  inverter_catalog_id?: string;
  additional_costs: [];
}

export interface PVQuantity {
  value: string;
  unit: string;
}

export interface PVModuleOption {
  catalog_id: string;
  manufacturer: string;
  model: string;
  module_power_wp: string;
  module_quantity: number;
  installed_power_kwp: string;
  unit_price_brl: string;
  total_price_brl: string;
}

export interface PVStringArrangement {
  mppt_id: number;
  module_quantity: number;
  voc_v: string;
  vmp_v: string;
}

export interface PVCompatibleInverter {
  catalog_id: string;
  manufacturer: string;
  model: string;
  inverter_type: string;
  battery_compatible: boolean;
  unit_price_brl: string;
  installed_pv_power_w: string;
  arrangement: PVStringArrangement[];
}

export interface PVStorage {
  storage_requested: boolean;
  daily_consumption: PVQuantity;
  autonomy: PVQuantity;
  autonomy_energy: PVQuantity;
  battery_efficiency: PVQuantity;
  battery_catalog_id: string | null;
  depth_of_discharge: PVQuantity;
  required_nominal_capacity: PVQuantity;
  battery_quantity: number;
  installed_nominal_capacity: PVQuantity;
  installed_deliverable_energy: PVQuantity;
  total_battery_cost: PVQuantity;
}

export interface PVBOMItem {
  category: 'module' | 'inverter' | 'battery' | 'additional';
  description: string;
  quantity: number;
  unit: string;
  unit_price_brl: string;
  subtotal_brl: string;
  catalog_id: string | null;
  manufacturer: string | null;
  model: string | null;
  supplier: string | null;
  source_url: string | null;
}

export interface PVBudget {
  currency: string;
  items: PVBOMItem[];
  modules_cost_brl: string;
  inverter_cost_brl: string;
  batteries_cost_brl: string;
  additional_cost_brl: string;
  equipment_cost_brl: string;
  total_cost_brl: string;
}

export interface PVSimulation {
  property_id: number;
  calculation: {
    reference_consumption: PVQuantity;
    target_offset: PVQuantity;
    hsp: PVQuantity;
    period_days: PVQuantity;
    performance_ratio: PVQuantity;
    target_energy: PVQuantity;
    required_pv_power: PVQuantity;
  };
  module_alternatives: PVModuleOption[];
  selected_module: PVModuleOption;
  compatible_inverters: PVCompatibleInverter[];
  selected_inverter: PVCompatibleInverter | null;
  storage: PVStorage;
  budget: PVBudget | null;
  methodology_version: string;
  disclaimer: string;
}

export interface PVProposal {
  id: number;
  property_id: number;
  total_cost_brl: string;
  created_at: string;
}
