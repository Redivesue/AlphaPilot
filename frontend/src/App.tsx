import { Routes, Route, Navigate, useNavigate, useLocation } from "react-router-dom";
import { Layout, Menu } from "antd";
import {
  DashboardOutlined,
  DatabaseOutlined,
  RobotOutlined,
  CloudServerOutlined,
  LineChartOutlined,
  FileTextOutlined,
  UnorderedListOutlined,
} from "@ant-design/icons";
import type { MenuProps } from "antd";

import Dashboard from "./pages/Dashboard";
import FactorLibrary from "./pages/FactorLibrary";
import FactorDetail from "./pages/FactorDetail";
import AgentConsole from "./pages/AgentConsole";
import DataManager from "./pages/DataManager";
import Backtesting from "./pages/Backtesting";
import Reports from "./pages/Reports";
import ReportDetail from "./pages/ReportDetail";
import SystemLogs from "./pages/SystemLogs";

const { Header, Sider, Content } = Layout;

const menuItems: MenuProps["items"] = [
  { key: "/", icon: <DashboardOutlined />, label: "Dashboard" },
  { key: "/factors", icon: <DatabaseOutlined />, label: "Factor Library" },
  { key: "/agent", icon: <RobotOutlined />, label: "Agent Console" },
  { key: "/data", icon: <CloudServerOutlined />, label: "Data Manager" },
  { key: "/backtest", icon: <LineChartOutlined />, label: "Backtesting" },
  { key: "/reports", icon: <FileTextOutlined />, label: "Reports" },
  { key: "/logs", icon: <UnorderedListOutlined />, label: "System Logs" },
];

function AppLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const selectedKey = location.pathname === "/" ? "/" : location.pathname.startsWith("/reports/") ? "/reports" : location.pathname;

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Sider theme="dark" width={220}>
        <div style={{ height: 64, display: "flex", alignItems: "center", paddingLeft: 24, color: "#fff", fontSize: 18, fontWeight: 600 }}>
          AlphaPilot
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[selectedKey]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          style={{ borderRight: 0 }}
        />
      </Sider>
      <Layout>
        <Header style={{ padding: "0 24px", background: "#fff", borderBottom: "1px solid #f0f0f0" }}>
          <span style={{ fontSize: 16, fontWeight: 500 }}>AlphaPilot Quant Research Platform</span>
        </Header>
        <Content style={{ margin: 24, padding: 24, background: "#fff", borderRadius: 8, minHeight: 280 }}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/factors" element={<FactorLibrary />} />
            <Route path="/factors/:id" element={<FactorDetail />} />
            <Route path="/agent" element={<AgentConsole />} />
            <Route path="/data" element={<DataManager />} />
            <Route path="/backtest" element={<Backtesting />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="/reports/:filename" element={<ReportDetail />} />
            <Route path="/logs" element={<SystemLogs />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  );
}

export default function App() {
  return <AppLayout />;
}
