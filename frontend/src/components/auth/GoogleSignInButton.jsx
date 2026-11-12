import React, { useEffect, useRef, useState } from 'react';
import { Info, ExternalLink } from 'lucide-react';
import { TennisAPI } from '../../services/api';

export default function GoogleSignInButton({ mode = 'signin', onSuccess, onError }) {
  const buttonContainerRef = useRef(null);
  const [clientId, setClientId] = useState(import.meta.env.VITE_GOOGLE_CLIENT_ID || '');
  const [gsiReady, setGsiReady] = useState(false);
  const [showSetupGuide, setShowSetupGuide] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let mounted = true;
    async function loadProvider() {
      const providers = await TennisAPI.getAuthProviders();
      const resolvedId = import.meta.env.VITE_GOOGLE_CLIENT_ID || providers?.google_client_id || '';
      if (mounted && resolvedId && !resolvedId.includes('your_')) {
        setClientId(resolvedId);
      }
    }
    loadProvider();
    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    if (!clientId) return;

    const handleCredentialResponse = async (response) => {
      if (!response?.credential) return;
      setLoading(true);
      try {
        const data = await TennisAPI.googleLogin(response.credential);
        onSuccess?.(data);
      } catch (err) {
        onError?.(err.response?.data?.detail || 'Google authentication failed.');
      } finally {
        setLoading(false);
      }
    };

    const initializeGSI = () => {
      if (!window.google?.accounts?.id || !buttonContainerRef.current) return;
      window.google.accounts.id.initialize({
        client_id: clientId,
        callback: handleCredentialResponse,
      });
      buttonContainerRef.current.innerHTML = '';
      window.google.accounts.id.renderButton(buttonContainerRef.current, {
        theme: 'filled_black',
        size: 'large',
        shape: 'pill',
        text: mode === 'signup' ? 'signup_with' : 'continue_with',
        width: 360,
      });
      setGsiReady(true);
    };

    if (window.google?.accounts?.id) {
      initializeGSI();
      return;
    }

    const existingScript = document.querySelector('script[src="https://accounts.google.com/gsi/client"]');
    if (existingScript) {
      existingScript.addEventListener('load', initializeGSI);
      return () => existingScript.removeEventListener('load', initializeGSI);
    }

    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    script.onload = initializeGSI;
    document.body.appendChild(script);
  }, [clientId, mode, onSuccess, onError]);

  if (clientId) {
    return (
      <div className="space-y-2">
        <div className="flex justify-center min-h-[44px]">
          <div ref={buttonContainerRef} className={loading ? 'opacity-60 pointer-events-none' : ''} />
        </div>
        {!gsiReady && (
          <div className="text-center text-[11px] text-textMuted">Loading Google Sign-In...</div>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-2.5">
      <button
        type="button"
        onClick={() => setShowSetupGuide((prev) => !prev)}
        className="w-full py-2.5 px-4 rounded-xl bg-white/5 hover:bg-white/10 border border-slateBorder text-white font-semibold text-sm transition flex items-center justify-center gap-3"
      >
        <svg className="w-4 h-4" viewBox="0 0 24 24" aria-hidden="true">
          <path fill="#4285F4" d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.82-2.4 3.68v3.05h3.88c2.27-2.09 3.665-5.17 3.665-9.17Z" />
          <path fill="#34A853" d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.11-6.72-4.96H1.29v3.14C3.26 21.3 7.31 24 12 24Z" />
          <path fill="#FBBC05" d="M5.28 14.24c-.24-.72-.38-1.49-.38-2.24s.14-1.52.38-2.24V6.62H1.29C.47 8.24 0 10.06 0 12s.47 3.76 1.29 5.38l3.99-3.14Z" />
          <path fill="#EA4335" d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.31 0 3.26 2.7 1.29 6.62l3.99 3.14c.95-2.85 3.6-4.96 6.72-4.96Z" />
        </svg>
        <span>{mode === 'signup' ? 'Register with Google' : 'Continue with Google'}</span>
      </button>

      {showSetupGuide && (
        <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-[11px] text-amber-200 space-y-1.5">
          <div className="flex items-center gap-1.5 font-semibold text-amber-300">
            <Info className="w-3.5 h-3.5 shrink-0" />
            <span>Google OAuth Client ID Setup Required (Free)</span>
          </div>
          <p className="text-amber-100/80 leading-relaxed">
            1. Create a free Web OAuth 2.0 Client ID in{' '}
            <a
              href="https://console.cloud.google.com/apis/credentials"
              target="_blank"
              rel="noreferrer"
              className="underline inline-flex items-center gap-0.5 text-tennis-green"
            >
              Google Cloud Console <ExternalLink className="w-2.5 h-2.5" />
            </a>
            <br />
            2. Add <code className="text-white">http://localhost:5173</code> to Authorized JavaScript origins.
            <br />
            3. Set <code className="text-white">GOOGLE_CLIENT_ID</code> in <code className="text-white">.env</code> and <code className="text-white">VITE_GOOGLE_CLIENT_ID</code> in <code className="text-white">frontend/.env</code>.
          </p>
        </div>
      )}
    </div>
  );
}
