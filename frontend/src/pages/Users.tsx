import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useState } from "react";
import { api, apiErrorMessage } from "../lib/api";
import type { User } from "../types";

const ROLES = ["ADMIN", "OPERATOR", "VIEWER"];

export default function Users() {
  const qc = useQueryClient();
  const [form, setForm] = useState({ username: "", password: "", role: "VIEWER" });
  const [error, setError] = useState("");

  const { data: users = [] } = useQuery({
    queryKey: ["users"],
    queryFn: async () => (await api.get<User[]>("/users")).data,
  });

  const create = useMutation({
    mutationFn: async () => (await api.post("/users", form)).data,
    onSuccess: () => {
      setError("");
      setForm({ username: "", password: "", role: "VIEWER" });
      qc.invalidateQueries({ queryKey: ["users"] });
    },
    onError: (e) => setError(apiErrorMessage(e)),
  });

  const toggleActive = useMutation({
    mutationFn: async ({ id, is_active }: { id: number; is_active: boolean }) =>
      (await api.patch(`/users/${id}`, { is_active })).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["users"] }),
    onError: (e) => setError(apiErrorMessage(e)),
  });

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!form.username || !form.password) return;
    create.mutate();
  }

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Utilisateurs & permissions</h1>

      <form onSubmit={onSubmit} className="flex flex-wrap items-end gap-3 rounded-xl border border-slate-800 bg-slate-900 p-4">
        <div>
          <label className="mb-1 block text-xs text-slate-400">Utilisateur</label>
          <input
            value={form.username}
            onChange={(e) => setForm({ ...form, username: e.target.value })}
            className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs text-slate-400">Mot de passe</label>
          <input
            type="password"
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs text-slate-400">Rôle</label>
          <select
            value={form.role}
            onChange={(e) => setForm({ ...form, role: e.target.value })}
            className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
          >
            {ROLES.map((r) => (
              <option key={r}>{r}</option>
            ))}
          </select>
        </div>
        <button className="rounded-md bg-emerald-600 px-4 py-2 text-sm hover:bg-emerald-500">Créer</button>
        {error && <span className="text-sm text-red-400">{error}</span>}
      </form>

      <div className="overflow-hidden rounded-xl border border-slate-800">
        <table className="w-full text-sm">
          <thead className="bg-slate-900 text-left text-slate-400">
            <tr>
              {["Utilisateur", "Nom complet", "Rôle", "Statut", "Créé le", ""].map((h) => (
                <th key={h} className="px-4 py-3">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800 bg-slate-950">
            {users.map((u) => (
              <tr key={u.id}>
                <td className="px-4 py-3 font-medium">{u.username}</td>
                <td className="px-4 py-3 text-slate-400">{u.full_name ?? "—"}</td>
                <td className="px-4 py-3">
                  <span className="rounded bg-slate-800 px-2 py-0.5 text-xs">{u.role.name}</span>
                </td>
                <td className={`px-4 py-3 ${u.is_active ? "text-emerald-400" : "text-red-400"}`}>
                  {u.is_active ? "actif" : "désactivé"}
                </td>
                <td className="px-4 py-3 text-slate-400">{new Date(u.created_at).toLocaleDateString()}</td>
                <td className="px-4 py-3 text-right">
                  <button
                    onClick={() => toggleActive.mutate({ id: u.id, is_active: !u.is_active })}
                    className="rounded border border-slate-700 px-2 py-1 text-xs hover:bg-slate-800"
                  >
                    {u.is_active ? "Désactiver" : "Activer"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
