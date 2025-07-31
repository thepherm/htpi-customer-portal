// Patient types
export interface Patient {
  id?: string;
  org_id?: string;
  mrn?: string;
  first_name: string;
  middle_name?: string;
  last_name: string;
  date_of_birth: string;
  gender: 'M' | 'F' | 'O';
  ssn?: string;
  
  // Contact information
  address_line1?: string;
  address_line2?: string;
  city?: string;
  state?: string;
  zip_code?: string;
  phone?: string;
  email?: string;
  
  // Emergency contact
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
  emergency_contact_relationship?: string;
  
  // Clinical information
  primary_care_physician?: string;
  referring_physician?: string;
  allergies?: string[];
  medications?: string[];
  medical_history?: string[];
  
  // Status
  status?: 'active' | 'inactive' | 'deceased';
  created_at?: string;
  updated_at?: string;
}

// Insurance types
export interface Insurance {
  id?: string;
  patient_id: string;
  coverage_order: 'primary' | 'secondary' | 'tertiary';
  
  // Insurance company
  insurance_company: string;
  plan_name?: string;
  plan_type?: 'HMO' | 'PPO' | 'EPO' | 'POS' | 'HDHP' | 'Other';
  
  // Policy information
  policy_number: string;
  group_number?: string;
  
  // Subscriber information
  subscriber_first_name: string;
  subscriber_last_name: string;
  subscriber_dob: string;
  subscriber_relationship: 'self' | 'spouse' | 'child' | 'other';
  
  // Coverage details
  effective_date: string;
  termination_date?: string;
  copay_amount?: number;
  deductible_amount?: number;
  out_of_pocket_max?: number;
  
  // Authorization
  prior_auth_required?: boolean;
  authorizations?: Authorization[];
  
  // Verification
  last_verified?: string;
  verification_status?: 'verified' | 'pending' | 'failed';
  
  created_at?: string;
  updated_at?: string;
}

export interface Authorization {
  auth_number: string;
  service_type: string;
  start_date: string;
  end_date: string;
  visits_authorized?: number;
  visits_used?: number;
  status: 'active' | 'expired' | 'cancelled';
}

// Form types
export interface HCFAForm {
  id?: string;
  patient_id: string;
  status: 'draft' | 'completed' | 'submitted' | 'accepted' | 'rejected';
  
  // Service facility
  service_facility_name?: string;
  service_facility_address?: string;
  service_facility_city?: string;
  service_facility_state?: string;
  service_facility_zip?: string;
  service_facility_npi?: string;
  
  // Billing provider
  billing_provider_name?: string;
  billing_provider_address?: string;
  billing_provider_city?: string;
  billing_provider_state?: string;
  billing_provider_zip?: string;
  billing_provider_phone?: string;
  billing_provider_npi?: string;
  billing_provider_tax_id?: string;
  
  // Service lines
  service_lines: ServiceLine[];
  
  // Diagnosis codes
  diagnosis_codes: string[];
  
  // Totals
  total_charge?: number;
  amount_paid?: number;
  balance_due?: number;
  
  // Dates
  statement_date?: string;
  service_date?: string;
  
  // Submission
  submitted_at?: string;
  claim_number?: string;
  
  created_at?: string;
  updated_at?: string;
}

export interface ServiceLine {
  line_number: number;
  date_of_service: string;
  place_of_service: string;
  cpt_code: string;
  modifier?: string;
  diagnosis_pointer: string;
  charges: number;
  units: number;
  rendering_provider_npi?: string;
}

// Claim types
export interface Claim {
  id?: string;
  form_id: string;
  patient_id: string;
  claim_number?: string;
  status: 'pending' | 'submitted' | 'accepted' | 'rejected' | 'paid' | 'denied';
  
  // Amounts
  billed_amount: number;
  allowed_amount?: number;
  paid_amount?: number;
  patient_responsibility?: number;
  
  // Dates
  submitted_date?: string;
  processed_date?: string;
  paid_date?: string;
  
  // Payer info
  payer_name?: string;
  payer_claim_number?: string;
  
  // Response
  rejection_reason?: string;
  era_number?: string;
  
  created_at?: string;
  updated_at?: string;
}

// User types
export interface User {
  id: string;
  org_id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: 'owner' | 'admin' | 'biller' | 'provider' | 'staff' | 'read_only';
  permissions: string[];
  status: 'active' | 'inactive' | 'suspended';
  last_login?: string;
  created_at: string;
}

// Auth types
export interface LoginCredentials {
  email: string;
  password: string;
}

export interface AuthResponse {
  token: string;
  user: User;
}

// API response types
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
  };
}

// Pagination
export interface PaginationParams {
  page?: number;
  limit?: number;
  sort?: string;
  order?: 'asc' | 'desc';
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  limit: number;
  totalPages: number;
}