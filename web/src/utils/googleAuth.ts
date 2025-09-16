import { API_BASE } from '../config'

declare global {
  interface Window {
    google: any;
  }
}

export interface GoogleUser {
  email: string;
  name: string;
  picture?: string;
  given_name?: string;
  family_name?: string;
}

export const initializeGoogleAuth = (): Promise<void> => {
  return new Promise((resolve, reject) => {
    if (window.google) {
      resolve();
      return;
    }

    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error('Failed to load Google Auth script'));
    document.head.appendChild(script);
  });
};

export const signInWithGoogle = (): Promise<GoogleUser> => {
  return new Promise((resolve, reject) => {
    if (!window.google) {
      reject(new Error('Google Auth not initialized'));
      return;
    }

    const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
    if (!clientId) {
      reject(new Error('Google Client ID not configured'));
      return;
    }

    window.google.accounts.id.initialize({
      client_id: clientId,
      callback: async (response: any) => {
        try {
          // Send the ID token to our backend
          const res = await fetch(`${API_BASE}/auth/google`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id_token: response.credential })
          });

          if (!res.ok) {
            const error = await res.json().catch(() => ({}));
            throw new Error(error.detail || `Authentication failed: ${res.status}`);
          }

          const userData = await res.json();
          
          // Store user info in localStorage
          localStorage.setItem('auth_user', userData.email);
          
          // Trigger storage event for same-tab updates
          window.dispatchEvent(new StorageEvent('storage', {
            key: 'auth_user',
            newValue: userData.email,
            storageArea: localStorage
          }));

          resolve({
            email: userData.email,
            name: userData.profile?.full_name || userData.email,
            given_name: userData.profile?.first_name,
            family_name: userData.profile?.last_name
          });
        } catch (error) {
          reject(error);
        }
      }
    });

    // Show the One Tap dialog
    window.google.accounts.id.prompt((notification: any) => {
      if (notification.isNotDisplayed() || notification.isSkippedMoment()) {
        // Fallback to popup if One Tap is not available
        window.google.accounts.id.renderButton(
          document.getElementById('google-signin-button'),
          { theme: 'outline', size: 'large', width: '100%' }
        );
      }
    });
  });
};

export const renderGoogleButton = (elementId: string, callback: (user: GoogleUser) => void) => {
  const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
  if (!clientId || !window.google) {
    console.error('Google Auth not properly configured');
    return;
  }

  window.google.accounts.id.initialize({
    client_id: clientId,
    callback: async (response: any) => {
      try {
        // Send the ID token to our backend
        const res = await fetch(`${API_BASE}/auth/google`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ id_token: response.credential })
        });

        if (!res.ok) {
          const error = await res.json().catch(() => ({}));
          throw new Error(error.detail || `Authentication failed: ${res.status}`);
        }

        const userData = await res.json();
        
        // Store user info in localStorage
        localStorage.setItem('auth_user', userData.email);
        
        // Trigger storage event for same-tab updates
        window.dispatchEvent(new StorageEvent('storage', {
          key: 'auth_user',
          newValue: userData.email,
          storageArea: localStorage
        }));

        callback({
          email: userData.email,
          name: userData.profile?.full_name || userData.email,
          given_name: userData.profile?.first_name,
          family_name: userData.profile?.last_name
        });
      } catch (error) {
        console.error('Google authentication error:', error);
        throw error;
      }
    }
  });

  window.google.accounts.id.renderButton(
    document.getElementById(elementId),
    { 
      theme: 'outline', 
      size: 'large', 
      width: '100%',
      text: 'signin_with'
    }
  );
};
