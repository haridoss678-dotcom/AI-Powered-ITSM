import { Navigate, Route, Routes } from 'react-router-dom';
import Layout from './components/Layout';
import { EmployeeProvider } from './context/EmployeeContext';
import AIAnalysisPage from './pages/AIAnalysisPage';
import DashboardPage from './pages/DashboardPage';
import DashboardTicketDetailsPage from './pages/DashboardTicketDetailsPage';
import EmployeeSelfServicePage from './pages/EmployeeSelfServicePage';
import KnowledgeBasePage from './pages/KnowledgeBasePage';
import SelfHealPage from './pages/SelfHealPage';
import SoftwareCataloguePage from './pages/SoftwareCataloguePage';
import TicketIntakePage from './pages/TicketIntakePage';

export default function App() {
  return (
    <EmployeeProvider>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Navigate to="/self-service" replace />} />
          {/* Screen 1: Employee Self-Service */}
          <Route path="/self-service" element={<EmployeeSelfServicePage />} />
          {/* Screen 2: Ticket Intake */}
          <Route path="/intake" element={<TicketIntakePage />} />
          {/* Screen 3: Self-Heal Agent */}
          <Route path="/self-heal" element={<SelfHealPage />} />
          {/* Screen 4: Knowledge Base */}
          <Route path="/knowledge" element={<KnowledgeBasePage />} />
          {/* Screen 5: Software Catalogue */}
          <Route path="/software" element={<SoftwareCataloguePage />} />
          {/* Screen 6: ITSM Dashboard */}
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/dashboard/tickets" element={<DashboardTicketDetailsPage />} />
          <Route path="/dashboard/tickets/:ticketId" element={<DashboardTicketDetailsPage />} />
          {/* Screen 7: AI Analysis */}
          <Route path="/analysis" element={<AIAnalysisPage />} />
          {/* Fallback */}
          <Route path="*" element={<Navigate to="/self-service" replace />} />
        </Route>
      </Routes>
    </EmployeeProvider>
  );
}
