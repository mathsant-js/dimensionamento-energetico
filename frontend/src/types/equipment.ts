export interface Equipment {
  id: number;
  name: string;
  category: string;
  power_watts: number;
  created_at: string;
}

export interface PropertyEquipment {
  id: number;
  property_id: number;
  equipment_id: number;
  quantity: number;
  hours_per_day: number;
  created_at: string;
}

export interface PropertyEquipmentWithDetails extends PropertyEquipment {
  equipment: Equipment;
}

export interface ConsumptionReportItem {
  id: number;
  equipment_name: string;
  power_watts: number;
  quantity: number;
  hours_per_day: number;
  monthly_consumption_kwh: number;
}

export interface ConsumptionReport {
  property_id: number;
  property_name: string;
  property_type: string;
  items: ConsumptionReportItem[];
  total_monthly_consumption_kwh: number;
  created_at: string;
}
