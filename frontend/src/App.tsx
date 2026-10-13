import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth/AuthContext";
import Layout from "./components/Layout";
import Alerts from "./pages/Alerts";
import Audit from "./pages/Audit";
import Backups from "./pages/Backups";
import Dashboard from "./pages/Dashboard";
import Infrastructure from "./pages/Infrastructure";
import Login from "./pages/Login";
import Proxmox from "./pages/Proxmox";
import Users from "./pages/Users";
import Veeam from "./pages/Veeam";

export default function App() {
  const { user, loading } = useAuth();

  if (loading) {
    return <div className="flex h-screen items-center justify-center text-slate-400">Chargement…</div>;
  }

  if (!user) {
    return (
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }

  const role = user.role.name;
  const canUsers = role === "ADMIN";
  const canAudit = role === "ADMIN" || role === "OPERATOR";

  return (
    <Routes>
      <Route path="/login" element={<Navigate to="/" replace />} />
      <Route element={<Layout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/infrastructure" element={<Infrastructure />} />
        <Route path="/proxmox" element={<Proxmox />} />
        <Route path="/backups" element={<Backups />} />
        <Route path="/veeam" element={<Veeam />} />
        <Route path="/alerts" element={<Alerts />} />
        {canAudit && <Route path="/audit" element={<Audit />} />}
        {canUsers && <Route path="/users" element={<Users />} />}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
