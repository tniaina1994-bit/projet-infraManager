import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "../lib/api";
import type { AuditEntry } from "../types";

export default function Audit() {
  const [username, setUsername] = useState("");
  const [action, setAction] = useState("");

  const { data: entries = [], isLoading } = useQuery({
    queryKey: ["audit", username, action],
    queryFn: async () =>
      (
        await api.get<AuditEntry[]>("/audit", {
          params: { ...(username ? { username } : {}), ...(action ? { action } : {}) },
        })
      ).data,
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Logs d'audit</h1>
        <div className="flex gap-2">
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="Utilisateur"
            className="rounded-md border border-slate-700 bg-slate-950 px-3 py-1.5 text-sm"
          />
          <input
            value={action}
            onChange={(e) => setAction(e.target.value)}
            placeholder="Action"
            className="rounded-md border border-slate-700 bg-slate-950 px-3 py-1.5 text-sm"
          />
        </div>
      </div>

      <div className="overflow-x-auto rounded-xl border border-slate-800">
        <table className="w-full text-sm">
          <thead className="bg-slate-900 text-left text-slate-400">
            <tr>
              {["Horodatage", "Utilisateur", "Action", "Ressource", "ID", "IP", "Résultat"].map((h) => (
                <th key={h} className="px-4 py-3">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800 bg-slate-950">
            {isLoading && (
              <tr>
                <td colSpan={7} className="px-4 py-6 text-center text-slate-500">
                  Chargement…
                </td>
              </tr>
            )}
            {entries.map((e) => (
              <tr key={e.id}>
                <td className="px-4 py-3 text-slate-400">{new Date(e.timestamp).toLocaleString()}</td>
                <td className="px-4 py-3 font-medium">{e.username}</td>
                <td className="px-4 py-3">{e.action}</td>
                <td className="px-4 py-3 text-slate-400">{e.resource ?? "—"}</td>
                <td className="px-4 py-3 text-slate-400">{e.resource_id ?? "—"}</td>
                <td className="px-4 py-3 text-slate-400">{e.ip_address ?? "—"}</td>
                <td className={`px-4 py-3 ${e.result === "SUCCESS" ? "text-emerald-400" : "text-red-400"}`}>
                  {e.result}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-slate-500">Les logs d'audit ne sont pas supprimables depuis l'interface.</p>
    </div>
  );
}
