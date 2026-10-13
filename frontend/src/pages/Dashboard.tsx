import { useQuery } from "@tanstack/react-query";
import {
  AlertTriangle,
  Boxes,
  Container,
  Cpu,
  HardDrive,
  Server,
  ServerOff,
  Monitor,
} from "lucide-react";
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../lib/api";
import type { DashboardSummary } from "../types";

function Stat({
  label,
  value,
  icon: Icon,
  tone = "text-white",
}: {
  label: string;
  value: number | string;
  icon: typeof Server;
  tone?: string;
}) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
      <div className="flex items-center justify-between">
        <span className="text-sm text-slate-400">{label}</span>
        <Icon className="h-4 w-4 text-slate-500" />
      </div>
      <div className={`mt-2 text-2xl font-semibold ${tone}`}>{value}</div>
    </div>
  );
}

export default function Dashboard() {
  const { data, isLoading } = useQuery({
    queryKey: ["dashboard"],
    queryFn: async () => (await api.get<DashboardSummary>("/dashboard/summary")).data,
  });

  if (isLoading || !data) return <div className="text-slate-400">Chargement du dashboard…</div>;

  const chart = [
    { name: "Datacenters", value: data.datacenters },
    { name: "Nodes", value: data.nodes },
    { name: "VMs", value: data.vms },
    { name: "Containers", value: data.containers },
    { name: "Repos", value: data.backup_repositories },
    { name: "Veeam", value: data.veeam_servers },
  ];

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Dashboard</h1>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <Stat label="Nodes online" value={`${data.nodes_online}/${data.nodes}`} icon={Server} />
        <Stat label="Nodes offline" value={data.nodes_offline} icon={ServerOff} tone="text-red-400" />
        <Stat label="VMs running" value={`${data.vms_running}/${data.vms}`} icon={Monitor} />
        <Stat label="Containers" value={data.containers} icon={Container} />
        <Stat label="Storage warnings" value={data.storage_warnings} icon={HardDrive} tone="text-amber-400" />
        <Stat label="Backup failures" value={data.backup_failures} icon={AlertTriangle} tone="text-red-400" />
        <Stat label="Backup warnings" value={data.backup_warnings} icon={AlertTriangle} tone="text-amber-400" />
        <Stat label="Backups running" value={data.running_backups} icon={Cpu} />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
          <h2 className="mb-4 flex items-center gap-2 text-sm font-medium text-slate-300">
            <Boxes className="h-4 w-4" /> Inventaire
          </h2>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={chart}>
              <XAxis dataKey="name" stroke="#64748b" fontSize={11} />
              <YAxis allowDecimals={false} stroke="#64748b" fontSize={11} />
              <Tooltip contentStyle={{ background: "#0f172a", border: "1px solid #334155" }} />
              <Bar dataKey="value" fill="#10b981" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
          <h2 className="mb-4 text-sm font-medium text-slate-300">Activité récente</h2>
          <ul className="space-y-2 text-sm">
            {data.recent_activity.length === 0 && <li className="text-slate-500">Aucune activité.</li>}
            {data.recent_activity.map((a, i) => (
              <li key={i} className="flex justify-between border-b border-slate-800 pb-2 text-slate-400">
                <span>
                  <span className="text-slate-200">{a.user}</span> — {a.action}
                  {a.resource ? ` (${a.resource})` : ""}
                </span>
                <span className="text-xs">{new Date(a.at).toLocaleString()}</span>
              </li>
            ))}
          </ul>
          <div className="mt-4 text-xs text-slate-500">
            Dernier backup réussi :{" "}
            {data.last_successful_backup ? new Date(data.last_successful_backup).toLocaleString() : "—"}
          </div>
        </div>
      </div>
    </div>
  );
}
