import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import DashboardLayout from './layouts/DashboardLayout';
import DashboardPage from './pages/DashboardPage';

// Lazy-load secondary routes so initial landing/dashboard bundle stays lightweight under high traffic
const LoginPage = lazy(() => import('./pages/LoginPage'));
const RegisterPage = lazy(() => import('./pages/RegisterPage'));
const PlayerExplorerPage = lazy(() => import('./pages/PlayerExplorerPage'));
const PlayerDetailPage = lazy(() => import('./pages/PlayerDetailPage'));
const ComparisonPage = lazy(() => import('./pages/ComparisonPage'));
const GlobalIntelligencePage = lazy(() => import('./pages/GlobalIntelligencePage'));
const CompetitionExplorerPage = lazy(() => import('./pages/CompetitionExplorerPage'));
const AIAssistantPage = lazy(() => import('./pages/AIAssistantPage'));
const WorkspacePage = lazy(() => import('./pages/WorkspacePage'));
const ReportsPage = lazy(() => import('./pages/ReportsPage'));
const DataQualityPage = lazy(() => import('./pages/DataQualityPage'));

function RouteLoader() {
  return (
    <div className="min-h-[60vh] flex items-center justify-center">
      <div className="w-8 h-8 rounded-full border-2 border-tennis-green border-t-transparent animate-spin" />
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<RouteLoader />}>
        <Routes>
          {/* PUBLIC MARKETING & AUTH */}
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

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
            path="/app/reports"
            element={
              <DashboardLayout>
                <ReportsPage />
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
      </Suspense>
    </BrowserRouter>
  );
}
