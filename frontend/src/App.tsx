import React, { useState, useEffect } from 'react';
import { useAuth, useUser, useClerk } from '@clerk/clerk-react';
import { Navbar } from './components/landing/Navbar';
import { HeroSection } from './components/landing/HeroSection';
import { InteractiveDemo } from './components/landing/InteractiveDemo';
import { CoreCapabilities } from './components/landing/CoreCapabilities';
import { ProcessSection } from './components/landing/ProcessSection';
import { EvidencePanelPreview } from './components/landing/EvidencePanelPreview';
import { Footer } from './components/landing/Footer';
import { WorkspaceLayout } from './components/workspace/WorkspaceLayout';
import { apiService, BackendStatus, setAuthTokenGetter } from './services/api';
import { Skiper21, AuthUser } from './components/auth/Skiper21';

export function App() {
  const [view, setView] = useState<'landing' | 'workspace'>('landing');
  const [selectedTicketId, setSelectedTicketId] = useState<string>('CMP-2026-9042');
  const [backendStatus, setBackendStatus] = useState<BackendStatus>({
    isLive: false,
    message: 'Checking backend status...',
    timestamp: new Date().toISOString(),
  });
  const [videoError, setVideoError] = useState(false);

  // Clerk Authentication State
  const { getToken, isSignedIn } = useAuth();
  const { user } = useUser();
  const clerk = useClerk();

  const [authUser, setAuthUser] = useState<AuthUser | null>(null);
  const [isAuthOpen, setIsAuthOpen] = useState<boolean>(false);

  // Bind live Clerk JWT token generator to API service
  useEffect(() => {
    setAuthTokenGetter(getToken);
  }, [getToken]);

  // Synchronize Clerk user identity to AuthUser
  useEffect(() => {
    if (isSignedIn && user) {
      setAuthUser({
        id: user.id,
        name: user.fullName || user.primaryEmailAddress?.emailAddress || 'Support Agent',
        identifier: user.primaryEmailAddress?.emailAddress || user.id,
        method: 'social',
        avatar: user.imageUrl,
      });
    } else {
      setAuthUser(null);
    }
  }, [isSignedIn, user]);

  useEffect(() => {
    apiService.checkHealth().then(setBackendStatus);
  }, []);

  const handleOpenAuth = () => {
    if (clerk?.openSignIn) {
      clerk.openSignIn();
    } else {
      setIsAuthOpen(true);
    }
  };

  const handleAuthSuccess = (authenticatedUser: AuthUser) => {
    setAuthUser(authenticatedUser);
    setIsAuthOpen(false);
  };

  const handleSignOut = () => {
    setAuthUser(null);
    try {
      localStorage.removeItem('policypulse_auth_user');
    } catch {
      // ignore
    }
  };

  const handleLaunchStudio = (ticketId?: string) => {
    if (ticketId) {
      setSelectedTicketId(ticketId);
    }
    setView('workspace');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleBackToLanding = () => {
    setView('landing');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  if (view === 'workspace') {
    return (
      <>
        <WorkspaceLayout
          onBackToLanding={handleBackToLanding}
          initialTicketId={selectedTicketId}
          backendStatus={backendStatus}
          authUser={authUser}
          onOpenAuth={handleOpenAuth}
        />
        <Skiper21
          open={isAuthOpen}
          onOpenChange={setIsAuthOpen}
          onSuccess={handleAuthSuccess}
        />
      </>
    );
  }

  return (
    <div className="min-h-screen bg-[#070b14] text-[#f1f1f5] flex flex-col selection:bg-white/20 selection:text-white">
      {/* Fullscreen Video Hero Viewport Container */}
      <div id="overview" className="relative min-h-screen overflow-hidden flex flex-col justify-start bg-[#070b14]">
        {/* Fullscreen Looping Video Background */}
        {!videoError ? (
          <video
            autoPlay
            loop
            muted
            playsInline
            onError={() => setVideoError(true)}
            className="absolute inset-0 z-0 h-full w-full object-cover"
          >
            <source
              src="https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260314_131748_f2ca2a28-fed7-44c8-b9a9-bd9acdd5ec31.mp4"
              type="video/mp4"
            />
          </video>
        ) : (
          <div className="absolute inset-0 z-0 bg-gradient-to-b from-[#0a1226] via-[#070b14] to-[#0a0f1d]" />
        )}

        {/* Cinematic Readability Dimmer Overlay */}
        <div className="absolute inset-0 z-0 bg-black/45 backdrop-brightness-[0.88] pointer-events-none" />

        {/* Transparent Glassmorphic Navigation */}
        <Navbar
          onLaunchStudio={() => handleLaunchStudio()}
          backendStatus={backendStatus}
          onOpenAuth={handleOpenAuth}
          authUser={authUser}
          onSignOut={handleSignOut}
        />

        {/* Fullscreen Centered Cinematic Hero */}
        <HeroSection onLaunchStudio={() => handleLaunchStudio()} />
      </div>

      {/* Product Explanation & Verification Sections Below Hero */}
      <main className="flex-1 bg-[#090D17]">
        <ProcessSection />

        <InteractiveDemo
          onLaunchStudioWithTicket={(ticketId) => handleLaunchStudio(ticketId)}
        />

        <CoreCapabilities />

        <EvidencePanelPreview />
      </main>

      <Footer onLaunchStudio={() => handleLaunchStudio()} />

      {/* Skiper21 Authentication Drawer */}
      <Skiper21
        open={isAuthOpen}
        onOpenChange={setIsAuthOpen}
        onSuccess={handleAuthSuccess}
      />
    </div>
  );
}

export default App;
