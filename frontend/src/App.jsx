import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import DashboardLayout from './layouts/DashboardLayout';
import DashboardPage from './pages/DashboardPage';
import PlayerExplorerPage from './pages/PlayerExplorerPage';
import PlayerDetailPage from './pages/PlayerDetailPage';
import ComparisonPage from './pages/ComparisonPage';
import GlobalIntelligencePage from './pages/GlobalIntelligencePage';
import CompetitionExplorerPage from './pages/CompetitionExplorerPage';
import AIAssistantPage from './pages/AIAssistantPage';
import WorkspacePage from './pages/WorkspacePage';
import DataQualityPage from './pages/DataQualityPage';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* PUBLIC MARKETING & AUTH */}
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />

        {/* PROTECTED / APPLICATION SAAS DASHBOARD */}
        <Route
          path="/app"
          element={
            <DashboardLayout>
              <DashboardPage />
            </DashboardLayout>
          }
        />
        <Route
          path="/app/players"
          element={
            <DashboardLayout>
              <PlayerExplorerPage />
            </DashboardLayout>
          }
        />
        <Route
          path="/app/players/:id"
          element={
            <DashboardLayout>
              <PlayerDetailPage />
            </DashboardLayout>
          }
        />
        <Route
          path="/app/compare"
          element={
            <DashboardLayout>
              <ComparisonPage />
            </DashboardLayout>
          }
        />
        <Route
          path="/app/global"
          element={
            <DashboardLayout>
              <GlobalIntelligencePage />
            </DashboardLayout>
          }
        />
        <Route
          path="/app/competitions"
          element={
            <DashboardLayout>
              <CompetitionExplorerPage />
            </DashboardLayout>
          }
        />
        <Route
          path="/app/assistant"
          element={
            <DashboardLayout>
              <AIAssistantPage />
            </DashboardLayout>
          }
        />
        <Route
          path="/app/workspace"
          element={
            <DashboardLayout>
              <WorkspacePage />
            </DashboardLayout>
          }
        />
        <Route
          path="/app/data-quality"
          element={
            <DashboardLayout>
              <DataQualityPage />
            </DashboardLayout>
          }
        />

        {/* CATCH-ALL REDIRECT */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
