import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";
import type { VeeamJob, VeeamServer } from "../types";

function statusColor(status: string) {
  if (["SUCCESS", "Success", "running"].includes(status)) return "text-emerald-400";
  if (["FAILED", "Failed"].includes(status)) return "text-red-400";
  if (["WARNING", "Warning"].includes(status)) return "text-amber-400";
  return "text-slate-400";
}

export default function Veeam() {
  const servers = useQuery({
    queryKey: ["veeam-servers"],
    queryFn: async () => (await api.get<VeeamServer[]>("/veeam/servers")).data,
  });
  const jobs = useQuery({
    queryKey: ["veeam-jobs"],
    queryFn: async () => (await api.get<VeeamJob[]>("/veeam/jobs")).data,
  });

  return (
    <div className="space-y-8">
      <h1 className="text-xl font-semibold">Veeam</h1>

      <section className="space-y-3">
        <h2 className="text-sm font-medium text-slate-300">Serveurs</h2>
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {(servers.data ?? []).map((s) => (
            <div key={s.id} className="rounded-xl border border-slate-800 bg-slate-900 p-4">
              <div className="flex justify-between">
                <span className="font-medium">{s.name}</span>
                <span className={`text-xs ${s.enabled ? "text-emerald-400" : "text-slate-500"}`}>
                  {s.enabled ? "enabled" : "disabled"}
                </span>
              </div>
              <div className="mt-1 text-sm text-slate-400">{s.api_url}</div>
              <div className="mt-2 text-xs text-slate-500">
                Dernière sync : {s.last_sync_at ? new Date(s.last_sync_at).toLocaleString() : "jamais"}
              </div>
            </div>
          ))}
          {(servers.data ?? []).length === 0 && (
            <div className="rounded-xl border border-dashed border-slate-800 p-6 text-center text-sm text-slate-500">
              Aucun serveur Veeam enregistré.
            </div>
          )}
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-sm font-medium text-slate-300">Jobs</h2>
        <div className="overflow-x-auto rounded-xl border border-slate-800">
          <table className="w-full text-sm">
            <thead className="bg-slate-900 text-left text-slate-400">
              <tr>
                {["Job Name", "Type", "Status", "Last Run", "Next Run", "Durée", "Transferred", "Backup Size"].map(
                  (h) => (
                    <th key={h} className="px-4 py-3">
                      {h}
                    </th>
                  ),
                )}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 bg-slate-950">
              {(jobs.data ?? []).map((j) => (
                <tr key={j.id}>
                  <td className="px-4 py-3 font-medium">{j.name}</td>
                  <td className="px-4 py-3 text-slate-400">{j.type ?? "—"}</td>
                  <td className={`px-4 py-3 ${statusColor(j.status)}`}>{j.status}</td>
                  <td className="px-4 py-3 text-slate-400">
                    {j.last_run_at ? new Date(j.last_run_at).toLocaleString() : "—"}
                  </td>
                  <td className="px-4 py-3 text-slate-400">
                    {j.next_run_at ? new Date(j.next_run_at).toLocaleString() : "—"}
                  </td>
                  <td className="px-4 py-3">{Math.round(j.duration_seconds / 60)} min</td>
                  <td className="px-4 py-3">{j.transferred_gb} GB</td>
                  <td className="px-4 py-3">{j.backup_size_gb} GB</td>
                </tr>
              ))}
              {(jobs.data ?? []).length === 0 && (
                <tr>
                  <td colSpan={8} className="px-4 py-6 text-center text-slate-500">
                    Aucun job Veeam synchronisé.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
