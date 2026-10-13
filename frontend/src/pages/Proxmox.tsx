import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api, apiErrorMessage } from "../lib/api";
import type { ContainerRow, NodeRow, ProxmoxServer, StorageRow, VMRow } from "../types";

const TABS = ["Nodes", "VMs", "Containers", "Storage", "Serveurs"] as const;
type Tab = (typeof TABS)[number];

const CRITICAL = new Set(["stop", "shutdown", "reboot"]);

function statusColor(status: string) {
  if (["running", "online", "active"].includes(status)) return "text-emerald-400";
  if (["stopped", "offline", "unknown"].includes(status)) return "text-slate-400";
  return "text-amber-400";
}

function fmtUptime(seconds: number) {
  if (!seconds) return "—";
  const d = Math.floor(seconds / 86400);
  const h = Math.floor((seconds % 86400) / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  return d > 0 ? `${d}j ${h}h` : h > 0 ? `${h}h ${m}m` : `${m}m`;
}

export default function Proxmox() {
  const [tab, setTab] = useState<Tab>("Nodes");
  const [message, setMessage] = useState("");
  const qc = useQueryClient();

  const nodes = useQuery({
    queryKey: ["px-nodes"],
    queryFn: async () => (await api.get<NodeRow[]>("/proxmox/nodes")).data,
    enabled: tab === "Nodes",
  });
  const vms = useQuery({
    queryKey: ["px-vms"],
    queryFn: async () => (await api.get<VMRow[]>("/proxmox/vms")).data,
    enabled: tab === "VMs",
  });
  const cts = useQuery({
    queryKey: ["px-cts"],
    queryFn: async () => (await api.get<ContainerRow[]>("/proxmox/containers")).data,
    enabled: tab === "Containers",
  });
  const storages = useQuery({
    queryKey: ["px-storage"],
    queryFn: async () => (await api.get<StorageRow[]>("/proxmox/storage")).data,
    enabled: tab === "Storage",
  });
  const servers = useQuery({
    queryKey: ["px-servers"],
    queryFn: async () => (await api.get<ProxmoxServer[]>("/proxmox/servers")).data,
  });

  function openConsole(kind: "kvm" | "lxc", vmid: number, name: string, node?: string | null) {
    const base = (servers.data?.[0]?.api_url ?? "").replace(/\/$/, "");
    if (!base) {
      setMessage("Aucun serveur Proxmox configuré");
      return;
    }
    if (!node) {
      setMessage("Node inconnu pour cette machine");
      return;
    }
    // Deep-link noVNC de Proxmox (source : openVNCViewer dans pvemanagerlib.js)
    const qs = new URLSearchParams({
      console: kind,
      novnc: "1",
      vmid: String(vmid),
      vmname: name,
      node,
      resize: "off",
    });
    window.open(`${base}/?${qs}`, "_blank", "width=810,height=560");
  }

  const action = useMutation({
    mutationFn: async ({ kind, id, act }: { kind: "vms" | "containers"; id: number; act: string }) =>
      (
        await api.post(`/proxmox/${kind}/${id}/action`, {
          action: act,
          confirm: true,
        })
      ).data,
    onSuccess: (data) => {
      setMessage(data.detail ?? "OK");
      qc.invalidateQueries({ queryKey: ["px-vms"] });
      qc.invalidateQueries({ queryKey: ["px-cts"] });
    },
    onError: (e) => setMessage(apiErrorMessage(e)),
  });

  const sync = useMutation({
    mutationFn: async () => (await api.post("/proxmox/sync")).data,
    onSuccess: () => {
      setMessage("Synchronisation lancée");
      qc.invalidateQueries();
    },
    onError: (e) => setMessage(apiErrorMessage(e)),
  });

  function runAction(kind: "vms" | "containers", id: number, act: string) {
    if (CRITICAL.has(act)) {
      const label = kind === "vms" ? "VM" : "container";
      if (!window.confirm(`Are you sure you want to ${act} ${label} ${id}?`)) return;
    }
    action.mutate({ kind, id, act });
  }

  const actions = ["start", "stop", "shutdown", "reboot"];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Proxmox</h1>
        <button
          onClick={() => sync.mutate()}
          disabled={sync.isPending}
          className="rounded-md bg-emerald-600 px-4 py-2 text-sm hover:bg-emerald-500 disabled:opacity-50"
        >
          {sync.isPending ? "Sync…" : "Synchroniser maintenant"}
        </button>
      </div>

      {message && <div className="rounded-md bg-slate-900 px-3 py-2 text-sm text-slate-300">{message}</div>}

      <div className="flex gap-2">
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`rounded-md px-3 py-1.5 text-sm ${
              tab === t ? "bg-slate-800 text-white" : "text-slate-400 hover:bg-slate-900"
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      <div className="overflow-x-auto rounded-xl border border-slate-800">
        {tab === "Nodes" && (
          <table className="w-full text-sm">
            <thead className="bg-slate-900 text-left text-slate-400">
              <tr>
                {["Hostname", "Status", "CPU", "RAM", "Disk", "Uptime", "Kernel", "Version"].map((h) => (
                  <th key={h} className="px-4 py-3">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 bg-slate-950">
              {(nodes.data ?? []).map((n) => (
                <tr key={n.id}>
                  <td className="px-4 py-3 font-medium">{n.name}</td>
                  <td className={`px-4 py-3 ${statusColor(n.status)}`}>{n.status}</td>
                  <td className="px-4 py-3">{n.cpu_usage}%</td>
                  <td className="px-4 py-3">{n.ram_usage}%</td>
                  <td className="px-4 py-3">{n.disk_usage}%</td>
                  <td className="px-4 py-3">{fmtUptime(n.uptime_seconds)}</td>
                  <td className="px-4 py-3 text-slate-400">{n.kernel ?? "—"}</td>
                  <td className="px-4 py-3 text-slate-400">{n.version ?? "—"}</td>
                </tr>
              ))}
              {(nodes.data ?? []).length === 0 && (
                <tr>
                  <td colSpan={8} className="px-4 py-6 text-center text-slate-500">
                    Aucun node — lance une synchronisation.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}

        {tab === "VMs" && (
          <table className="w-full text-sm">
            <thead className="bg-slate-900 text-left text-slate-400">
              <tr>
                {["VMID", "Name", "Status", "CPU", "RAM", "Disk", "Uptime", "Actions"].map((h) => (
                  <th key={h} className="px-4 py-3">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 bg-slate-950">
              {(vms.data ?? []).map((vm) => (
                <tr key={vm.id}>
                  <td className="px-4 py-3">{vm.vmid}</td>
                  <td className="px-4 py-3 font-medium">{vm.name}</td>
                  <td className={`px-4 py-3 ${statusColor(vm.status)}`}>{vm.status}</td>
                  <td className="px-4 py-3">{vm.cpu_usage}%</td>
                  <td className="px-4 py-3">{Math.round(vm.ram_mb)} MB</td>
                  <td className="px-4 py-3">{vm.disk_gb} GB</td>
                  <td className="px-4 py-3">{fmtUptime(vm.uptime_seconds)}</td>
                  <td className="px-4 py-3">
                    <div className="flex gap-1">
                      <button
                        onClick={() => openConsole("kvm", vm.vmid, vm.name, vm.node_name)}
                        title="Ouvrir la console noVNC dans une nouvelle fenêtre"
                        className="rounded border border-emerald-700 px-2 py-1 text-xs text-emerald-400 hover:bg-emerald-950"
                      >
                        Console
                      </button>
                      {actions.map((act) => (
                        <button
                          key={act}
                          onClick={() => runAction("vms", vm.id, act)}
                          className="rounded border border-slate-700 px-2 py-1 text-xs hover:bg-slate-800"
                        >
                          {act}
                        </button>
                      ))}
                    </div>
                  </td>
                </tr>
              ))}
              {(vms.data ?? []).length === 0 && (
                <tr>
                  <td colSpan={8} className="px-4 py-6 text-center text-slate-500">
                    Aucune VM.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}

        {tab === "Containers" && (
          <table className="w-full text-sm">
            <thead className="bg-slate-900 text-left text-slate-400">
              <tr>
                {["CTID", "Name", "Status", "CPU", "RAM", "Disk", "Uptime", "Actions"].map((h) => (
                  <th key={h} className="px-4 py-3">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 bg-slate-950">
              {(cts.data ?? []).map((ct) => (
                <tr key={ct.id}>
                  <td className="px-4 py-3">{ct.ctid}</td>
                  <td className="px-4 py-3 font-medium">{ct.name}</td>
                  <td className={`px-4 py-3 ${statusColor(ct.status)}`}>{ct.status}</td>
                  <td className="px-4 py-3">{ct.cpu_usage}%</td>
                  <td className="px-4 py-3">{Math.round(ct.ram_mb)} MB</td>
                  <td className="px-4 py-3">{ct.disk_gb} GB</td>
                  <td className="px-4 py-3">{fmtUptime(ct.uptime_seconds)}</td>
                  <td className="px-4 py-3">
                    <div className="flex gap-1">
                      <button
                        onClick={() => openConsole("lxc", ct.ctid, ct.name, ct.node_name)}
                        title="Ouvrir la console noVNC dans une nouvelle fenêtre"
                        className="rounded border border-emerald-700 px-2 py-1 text-xs text-emerald-400 hover:bg-emerald-950"
                      >
                        Console
                      </button>
                      {actions.map((act) => (
                        <button
                          key={act}
                          onClick={() => runAction("containers", ct.id, act)}
                          className="rounded border border-slate-700 px-2 py-1 text-xs hover:bg-slate-800"
                        >
                          {act}
                        </button>
                      ))}
                    </div>
                  </td>
                </tr>
              ))}
              {(cts.data ?? []).length === 0 && (
                <tr>
                  <td colSpan={8} className="px-4 py-6 text-center text-slate-500">
                    Aucun container.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}

        {tab === "Storage" && (
          <table className="w-full text-sm">
            <thead className="bg-slate-900 text-left text-slate-400">
              <tr>
                {["Storage", "Type", "Total", "Used", "Free", "Usage %", "Status"].map((h) => (
                  <th key={h} className="px-4 py-3">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 bg-slate-950">
              {(storages.data ?? []).map((s) => (
                <tr key={s.id}>
                  <td className="px-4 py-3 font-medium">{s.name}</td>
                  <td className="px-4 py-3 text-slate-400">{s.type ?? "—"}</td>
                  <td className="px-4 py-3">{s.total_gb} GB</td>
                  <td className="px-4 py-3">{s.used_gb} GB</td>
                  <td className="px-4 py-3">{s.free_gb} GB</td>
                  <td className="px-4 py-3">
                    <span
                      className={
                        s.usage_percent >= 90 ? "text-red-400" : s.usage_percent >= 80 ? "text-amber-400" : ""
                      }
                    >
                      {s.usage_percent}%
                    </span>
                  </td>
                  <td className={`px-4 py-3 ${statusColor(s.status)}`}>{s.status}</td>
                </tr>
              ))}
              {(storages.data ?? []).length === 0 && (
                <tr>
                  <td colSpan={7} className="px-4 py-6 text-center text-slate-500">
                    Aucun storage.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}

        {tab === "Serveurs" && (
          <table className="w-full text-sm">
            <thead className="bg-slate-900 text-left text-slate-400">
              <tr>
                {["Nom", "URL", "Token ID", "TLS", "Dernière sync"].map((h) => (
                  <th key={h} className="px-4 py-3">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 bg-slate-950">
              {(servers.data ?? []).map((s) => (
                <tr key={s.id}>
                  <td className="px-4 py-3 font-medium">{s.name}</td>
                  <td className="px-4 py-3 text-slate-400">{s.api_url}</td>
                  <td className="px-4 py-3 text-slate-400">{s.token_id}</td>
                  <td className="px-4 py-3">{s.tls_verify ? "vérifié" : "ignoré"}</td>
                  <td className="px-4 py-3 text-slate-400">
                    {s.last_sync_at ? new Date(s.last_sync_at).toLocaleString() : "jamais"}
                  </td>
                </tr>
              ))}
              {(servers.data ?? []).length === 0 && (
                <tr>
                  <td colSpan={5} className="px-4 py-6 text-center text-slate-500">
                    Aucun serveur enregistré (seed depuis le .env au premier démarrage).
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
