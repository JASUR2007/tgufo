import React, { useState } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { QuickDemoBar } from './components/layout/QuickDemoBar';
import { Header } from './components/layout/Header';
import { Sidebar } from './components/layout/Sidebar';
import { AuthModal } from './components/auth/AuthModal';
import { VideoUploadModal } from './components/video/VideoUploadModal';

import { HomePage } from './pages/HomePage';
import { WatchPage } from './pages/WatchPage';
import { ChannelPage } from './pages/ChannelPage';
import { SearchPage } from './pages/SearchPage';
import { PlaylistsPage } from './pages/PlaylistsPage';
import { ModerationPage } from './pages/ModerationPage';

export const App: React.FC = () => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  return (
    <AuthProvider>
      <BrowserRouter>
        <div className="flex flex-col h-screen bg-[#0f0f0f] text-white overflow-hidden">
          {/* Quick 1-Click Role Switcher */}
          <QuickDemoBar />

          {/* YouTube Main Header */}
          <Header toggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)} />

          {/* App Body with Sidebar & Route Views */}
          <div className="flex flex-1 overflow-hidden">
            <Sidebar isOpen={isSidebarOpen} />
            <main className="flex-1 overflow-y-auto flex flex-col">
              <Routes>
                <Route path="/" element={<HomePage />} />
                <Route path="/watch/:videoId" element={<WatchPage />} />
                <Route path="/channel/:channelId" element={<ChannelPage />} />
                <Route path="/search" element={<SearchPage />} />
                <Route path="/playlists" element={<PlaylistsPage />} />
                <Route path="/moderation" element={<ModerationPage />} />
              </Routes>
            </main>
          </div>

          {/* Modals */}
          <AuthModal />
          <VideoUploadModal />
        </div>
      </BrowserRouter>
    </AuthProvider>
  );
};

export default App;
