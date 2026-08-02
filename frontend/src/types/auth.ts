export interface User {
  user_id: string;
  email: string;
  is_active: boolean;
  created_at: string;
}

export interface RegistrationResponse {
  user: User;
  development_notice: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}