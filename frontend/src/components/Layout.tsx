import {
  Activity,
  Boxes,
  Bell,
  Database,
  HardDrive,
  History,
  LayoutDashboard,
  LogOut,
  Server,
  ShieldCheck,
  Users as UsersIcon,
} from "lucide-react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

const nav = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/infrastructure", label: "Infrastructure", icon: Boxes },
  { to: "/proxmox", label: "Proxmox", icon: Server },
  { to: "/backups", label: "Backups", icon: HardDrive },
  { to: "/veeam", label: "Veeam", icon: Database },
  { to: "/alerts", label: "Alertes", icon: Bell },
  { to: "/audit", label: "Audit", icon: History, roles: ["ADMIN", "OPERATOR"] },
  { to: "/users", label: "Utilisateurs", icon: UsersIcon, roles: ["ADMIN"] },
];

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="flex h-screen">
      <aside className="flex w-60 flex-col border-r border-slate-800 bg-slate-900">
        <div className="flex items-center gap-2 px-5 py-5">
          <ShieldCheck className="h-6 w-6 text-emerald-400" />
          <span className="text-lg font-semibold">InfraManager</span>
        </div>
        <nav className="flex-1 space-y-1 px-3">
          {nav
            .filter((item) => !item.roles || (user && item.roles.includes(user.role.name)))
            .map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                end={to === "/"}
                className={({ isActive }) =>
                  `flex items-center gap-3 rounded-md px-3 py-2 text-sm transition ${
                    isActive ? "bg-slate-800 text-white" : "text-slate-400 hover:bg-slate-800/60 hover:text-white"
                  }`
                }
              >
                <Icon className="h-4 w-4" />
                {label}
              </NavLink>
            ))}
        </nav>
        <div className="border-t border-slate-800 px-4 py-4">
          <div className="flex items-center gap-2">
            <Activity className="h-4 w-4 text-emerald-400" />
            <div className="min-w-0">
              <div className="truncate text-sm">{user?.username}</div>
              <div className="text-xs text-slate-500">{user?.role.name}</div>
            </div>
          </div>
          <button
            onClick={async () => {
              await logout();
              navigate("/login");
            }}
            className="mt-3 flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-sm text-slate-400 hover:bg-slate-800 hover:text-white"
          >
            <LogOut className="h-4 w-4" /> Déconnexion
          </button>
        </div>
      </aside>
      <main className="flex-1 overflow-y-auto p-6">
        <Outlet />
      </main>
    </div>
  );
}
