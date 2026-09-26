export interface PropertyBase {
  identification: string;
  property_type: string;
  latitude?: number | null;
  longitude?: number | null;
  built_area?: number | null;
  roof_area?: number | null;
  orientation?: string | null;
  tilt_angle?: number | null;
}

export interface PropertyCreate extends PropertyBase {}

export interface PropertyUpdate {
  identification?: string;
  property_type?: string;
  address?: string | null;
  city?: string | null;
  state?: string | null;
  zipcode?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  built_area?: number | null;
  roof_area?: number | null;
  orientation?: string | null;
  tilt_angle?: number | null;
}

export interface PropertyRead extends PropertyBase {
  id: number;
  user_id: number;
  created_at: string; // ISO string
  updated_at?: string | null; // ISO string
}
