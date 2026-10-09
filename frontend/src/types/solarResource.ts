export interface SolarResource {
  id: number;
  property_id: number;
  hsp_kwh_m2_day: string;
  unit: 'kWh/m²/dia';
  source: string;
  source_date: string;
  acquisition_mode: 'manual';
  location_city?: string | null;
  location_state?: string | null;
  location_latitude?: string | null;
  location_longitude?: string | null;
  created_at: string;
  updated_at: string;
}

export interface SolarResourceInput {
  hsp_kwh_m2_day: number;
  unit: 'kWh/m²/dia';
  source: string;
  source_date: string;
  acquisition_mode: 'manual';
}
