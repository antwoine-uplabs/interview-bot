import { createClient } from '@supabase/supabase-js';

// Get Supabase credentials from environment variables
const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL || '';
const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY || '';

// Validate environment variables
if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
  console.error('Missing Supabase environment variables. Authentication will not work.');
}

// Create a single supabase client for the entire app
const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// This function is used for storing the Supabase session token 
// to be used in API requests to our FastAPI backend
export const storeAuthToken = (token: string) => {
  localStorage.setItem('supabase_auth_token', token);
};

// Clear the token when logging out
export const clearAuthToken = () => {
  localStorage.removeItem('supabase_auth_token');
};

export interface AuthUser {
  id: string;
  email: string;
  role?: string;
}

// Authentication functions
export const signUp = async (email: string, password: string): Promise<AuthUser | null> => {
  const { data, error } = await supabase.auth.signUp({
    email,
    password,
  });

  if (error) {
    console.error('Error signing up:', error.message);
    throw new Error(error.message);
  }

  if (data.session) {
    storeAuthToken(data.session.access_token);
    return {
      id: data.user!.id,
      email: data.user!.email!,
    };
  }

  return null;
};

export const signIn = async (email: string, password: string): Promise<AuthUser | null> => {
  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password,
  });

  if (error) {
    console.error('Error signing in:', error.message);
    throw new Error(error.message);
  }

  if (data.session) {
    storeAuthToken(data.session.access_token);
    return {
      id: data.user.id,
      email: data.user.email!,
    };
  }

  return null;
};

export const signOut = async (): Promise<void> => {
  const { error } = await supabase.auth.signOut();
  
  if (error) {
    console.error('Error signing out:', error.message);
    throw new Error(error.message);
  }
  
  clearAuthToken();
};

export const resetPassword = async (email: string): Promise<void> => {
  const { error } = await supabase.auth.resetPasswordForEmail(email);
  
  if (error) {
    console.error('Error resetting password:', error.message);
    throw new Error(error.message);
  }
};

export const getCurrentUser = async (): Promise<AuthUser | null> => {
  const { data, error } = await supabase.auth.getUser();
  
  if (error || !data.user) {
    return null;
  }
  
  return {
    id: data.user.id,
    email: data.user.email!,
  };
};

export default supabase;