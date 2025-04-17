import React, { useState, useEffect, ReactNode } from 'react';
import { getCurrentUser, signIn, signOut, signUp, AuthUser } from '../services/supabase';
import { AuthContext } from './AuthContext.types';

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadUser() {
      try {
        const currentUser = await getCurrentUser();
        setUser(currentUser);
      } catch (err) {
        console.error('Error loading user:', err);
      } finally {
        setLoading(false);
      }
    }
    
    loadUser();
  }, []);

  const handleSignIn = async (email: string, password: string) => {
    try {
      setError(null);
      const user = await signIn(email, password);
      setUser(user);
      return user;
    } catch (err) {
      const error = err instanceof Error ? err.message : 'An error occurred during sign in';
      setError(error);
      return null;
    }
  };

  const handleSignUp = async (email: string, password: string) => {
    try {
      setError(null);
      const user = await signUp(email, password);
      setUser(user);
      return user;
    } catch (err) {
      const error = err instanceof Error ? err.message : 'An error occurred during sign up';
      setError(error);
      return null;
    }
  };

  const handleSignOut = async () => {
    try {
      setError(null);
      await signOut();
      setUser(null);
    } catch (err) {
      const error = err instanceof Error ? err.message : 'An error occurred during sign out';
      setError(error);
    }
  };

  const value = {
    user,
    loading,
    signIn: handleSignIn,
    signUp: handleSignUp,
    signOut: handleSignOut,
    error
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// Hook is exported from separate file to avoid Fast Refresh warnings