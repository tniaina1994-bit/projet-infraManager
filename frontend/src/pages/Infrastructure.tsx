import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useState } from "react";
import { api, apiErrorMessage } from "../lib/api";
import type { Infrastructure } from "../types";

const ENVIRONMENTS = ["Production", "Staging", "Development", "Lab"];

export default function Infrastructure() {
  const qc = useQueryClient();
  const [form, setForm] = useState({ name: "", location: "", environment: "Production", provider: "" });
  const [error, setError] = useState("");

  const { data: infrastructures = [], isLoading } = useQuery({
    queryKey: ["infrastructures"],
    queryFn: async () => (await api.get<Infrastructure[]>("/infrastructures")).data,
  });

  const create = useMutation({
    mutationFn: async () =>
      (await api.post("/infrastructures", { ...form, api_endpoint: null, description: null })).data,
    onSuccess: () => {
      setError("");
      setForm({ name: "", location: "", environment: "Production", provider: "" });
      qc.invalidateQueries({ queryKey: ["infrastructures"] });
    },
    onError: (e) => setError(apiErrorMessage(e)),
  });

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!form.name.trim()) return;
    create.mutate();
  }

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Infrastructure</h1>

      <form onSubmit={onSubmit} className="flex flex-wrap items-end gap-3 rounded-xl border border-slate-800 bg-slate-900 p-4">
        <div>
          <label className="mb-1 block text-xs text-slate-400">Nom</label>
          <input
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
            placeholder="DC-Tana"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs text-slate-400">Localisation</label>
          <input
            value={form.location}
            onChange={(e) => setForm({ ...form, location: e.target.value })}
            className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
            placeholder="Antananarivo"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs text-slate-400">Environnement</label>
          <select
            value={form.environment}
            onChange={(e) => setForm({ ...form, environment: e.target.value })}
            className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
          >
            {ENVIRONMENTS.map((env) => (
              <option key={env}>{env}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="mb-1 block text-xs text-slate-400">Provider</label>
          <input
            value={form.provider}
            onChange={(e) => setForm({ ...form, provider: e.target.value })}
            className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
            placeholder="Proxmox"
          />
        </div>
        <button className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium hover:bg-emerald-500">
          Ajouter
        </button>
        {error && <span className="text-sm text-red-400">{error}</span>}
      </form>

      <div className="overflow-hidden rounded-xl border border-slate-800">
        <table className="w-full text-sm">
          <thead className="bg-slate-900 text-left text-slate-400">
            <tr>
              <th className="px-4 py-3">Nom</th>
              <th className="px-4 py-3">Environnement</th>
              <th className="px-4 py-3">Localisation</th>
              <th className="px-4 py-3">Provider</th>
              <th className="px-4 py-3">Statut</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800 bg-slate-950">
            {isLoading && (
              <tr>
                <td colSpan={5} className="px-4 py-6 text-center text-slate-500">
                  Chargement…
                </td>
              </tr>
            )}
            {!isLoading && infrastructures.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-6 text-center text-slate-500">
                  Aucune infrastructure — ajoute-en une ci-dessus.
                </td>
              </tr>
            )}
            {infrastructures.map((infra) => (
              <tr key={infra.id}>
                <td className="px-4 py-3 font-medium">{infra.name}</td>
                <td className="px-4 py-3">
                  <span className="rounded bg-slate-800 px-2 py-0.5 text-xs">{infra.environment}</span>
                </td>
                <td className="px-4 py-3 text-slate-400">{infra.location ?? "—"}</td>
                <td className="px-4 py-3 text-slate-400">{infra.provider ?? "—"}</td>
                <td className="px-4 py-3 text-slate-400">{infra.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
