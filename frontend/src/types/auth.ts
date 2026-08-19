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

export interface AuthSessionResponse {
  user: User;
  expires_in: number;
  development_notice: string;
}

export interface LogoutResponse {
  logged_out: boolean;
  message: string;
}