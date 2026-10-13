import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "../lib/api";
import type { BackupHistoryRow, BackupJob, BackupRepository } from "../types";

const STATUSES = ["SUCCESS", "WARNING", "FAILED", "RUNNING", "CANCELLED", "UNKNOWN"];

function statusColor(status: string) {
  if (status === "SUCCESS") return "text-emerald-400";
  if (status === "FAILED") return "text-red-400";
  if (status === "WARNING") return "text-amber-400";
  if (status === "RUNNING") return "text-sky-400";
  return "text-slate-400";
}

export default function Backups() {
  const [status, setStatus] = useState("");
  const [search, setSearch] = useState("");

  const jobs = useQuery({
    queryKey: ["backup-jobs", status, search],
    queryFn: async () =>
      (
        await api.get<BackupJob[]>("/backups/jobs", {
          params: { ...(status ? { status } : {}), ...(search ? { search } : {}) },
        })
      ).data,
  });

  const history = useQuery({
    queryKey: ["backup-history"],
    queryFn: async () => (await api.get<BackupHistoryRow[]>("/backups/history")).data,
  });

  const repos = useQuery({
    queryKey: ["backup-repos"],
    queryFn: async () => (await api.get<BackupRepository[]>("/backups/repositories")).data,
  });

  return (
    <div className="space-y-8">
      <h1 className="text-xl font-semibold">Backup Management</h1>

      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-medium text-slate-300">Backup Jobs</h2>
          <div className="flex gap-2">
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Rechercher…"
              className="rounded-md border border-slate-700 bg-slate-950 px-3 py-1.5 text-sm"
            />
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              className="rounded-md border border-slate-700 bg-slate-950 px-3 py-1.5 text-sm"
            >
              <option value="">Tous les statuts</option>
              {STATUSES.map((s) => (
                <option key={s}>{s}</option>
              ))}
            </select>
          </div>
        </div>
        <div className="overflow-x-auto rounded-xl border border-slate-800">
          <table className="w-full text-sm">
            <thead className="bg-slate-900 text-left text-slate-400">
              <tr>
                {["Name", "Source", "Target", "Schedule", "Server", "Status", "Last run", "Size"].map((h) => (
                  <th key={h} className="px-4 py-3">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 bg-slate-950">
              {(jobs.data ?? []).map((j) => (
                <tr key={j.id}>
                  <td className="px-4 py-3 font-medium">{j.name}</td>
                  <td className="px-4 py-3 text-slate-400">{j.source ?? "—"}</td>
                  <td className="px-4 py-3 text-slate-400">{j.target ?? "—"}</td>
                  <td className="px-4 py-3 text-slate-400">{j.schedule ?? "—"}</td>
                  <td className="px-4 py-3 text-slate-400">{j.server ?? "—"}</td>
                  <td className={`px-4 py-3 ${statusColor(j.status)}`}>{j.status}</td>
                  <td className="px-4 py-3 text-slate-400">
                    {j.last_run_at ? new Date(j.last_run_at).toLocaleString() : "—"}
                  </td>
                  <td className="px-4 py-3">{j.size_gb} GB</td>
                </tr>
              ))}
              {(jobs.data ?? []).length === 0 && (
                <tr>
                  <td colSpan={8} className="px-4 py-6 text-center text-slate-500">
                    Aucun job.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-sm font-medium text-slate-300">Backup History</h2>
        <div className="overflow-x-auto rounded-xl border border-slate-800">
          <table className="w-full text-sm">
            <thead className="bg-slate-900 text-left text-slate-400">
              <tr>
                {["Date", "Job", "VM", "Début", "Fin", "Durée", "Taille", "Transféré", "Status", "Erreur"].map(
                  (h) => (
                    <th key={h} className="px-4 py-3">
                      {h}
                    </th>
                  ),
                )}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 bg-slate-950">
              {(history.data ?? []).map((h) => (
                <tr key={h.id}>
                  <td className="px-4 py-3 text-slate-400">
                    {h.started_at ? new Date(h.started_at).toLocaleDateString() : "—"}
                  </td>
                  <td className="px-4 py-3">{h.job_name ?? "—"}</td>
                  <td className="px-4 py-3 text-slate-400">{h.vm ?? "—"}</td>
                  <td className="px-4 py-3 text-slate-400">
                    {h.started_at ? new Date(h.started_at).toLocaleTimeString() : "—"}
                  </td>
                  <td className="px-4 py-3 text-slate-400">
                    {h.ended_at ? new Date(h.ended_at).toLocaleTimeString() : "—"}
                  </td>
                  <td className="px-4 py-3">{Math.round(h.duration_seconds / 60)} min</td>
                  <td className="px-4 py-3">{h.backup_size_gb} GB</td>
                  <td className="px-4 py-3">{h.transferred_gb} GB</td>
                  <td className={`px-4 py-3 ${statusColor(h.status)}`}>{h.status}</td>
                  <td className="px-4 py-3 text-red-400">{h.error ?? ""}</td>
                </tr>
              ))}
              {(history.data ?? []).length === 0 && (
                <tr>
                  <td colSpan={10} className="px-4 py-6 text-center text-slate-500">
                    Aucun historique.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-sm font-medium text-slate-300">Repositories</h2>
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {(repos.data ?? []).map((r) => (
            <div key={r.id} className="rounded-xl border border-slate-800 bg-slate-900 p-4">
              <div className="flex justify-between">
                <span className="font-medium">{r.name}</span>
                <span className={`text-xs ${statusColor(r.status)}`}>{r.status}</span>
              </div>
              <div className="mt-3 h-2 overflow-hidden rounded bg-slate-800">
                <div
                  className={`h-full ${
                    r.usage_percent >= 90 ? "bg-red-500" : r.usage_percent >= 80 ? "bg-amber-500" : "bg-emerald-500"
                  }`}
                  style={{ width: `${Math.min(100, r.usage_percent)}%` }}
                />
              </div>
              <div className="mt-2 flex justify-between text-xs text-slate-400">
                <span>
                  {r.used_gb} / {r.total_capacity_gb} GB
                </span>
                <span>{r.usage_percent}%</span>
              </div>
            </div>
          ))}
          {(repos.data ?? []).length === 0 && (
            <div className="rounded-xl border border-dashed border-slate-800 p-6 text-center text-sm text-slate-500">
              Aucun repository.
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
