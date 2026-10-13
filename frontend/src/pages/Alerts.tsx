import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../lib/api";
import type { Alert } from "../types";

function severityColor(severity: string) {
  if (severity === "CRITICAL") return "bg-red-950 text-red-300";
  if (severity === "WARNING") return "bg-amber-950 text-amber-300";
  return "bg-slate-800 text-slate-300";
}

export default function Alerts() {
  const qc = useQueryClient();
  const { data: alerts = [] } = useQuery({
    queryKey: ["alerts"],
    queryFn: async () => (await api.get<Alert[]>("/alerts")).data,
    refetchInterval: 15_000,
  });

  const update = useMutation({
    mutationFn: async ({ id, status }: { id: number; status: string }) =>
      (await api.patch(`/alerts/${id}`, { status })).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["alerts"] }),
  });

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Alertes</h1>
      <div className="space-y-3">
        {alerts.length === 0 && (
          <div className="rounded-xl border border-dashed border-slate-800 p-6 text-center text-sm text-slate-500">
            Aucune alerte.
          </div>
        )}
        {alerts.map((a) => (
          <div key={a.id} className="rounded-xl border border-slate-800 bg-slate-900 p-4">
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="flex items-center gap-2">
                  <span className={`rounded px-2 py-0.5 text-xs ${severityColor(a.severity)}`}>{a.severity}</span>
                  <span className="font-medium">{a.title}</span>
                  <span className="text-xs text-slate-500">{a.alert_type}</span>
                </div>
                <p className="mt-1 text-sm text-slate-400">{a.description}</p>
                <div className="mt-1 text-xs text-slate-500">
                  {a.source} {a.resource ? `· ${a.resource}` : ""} · {new Date(a.timestamp).toLocaleString()}
                </div>
              </div>
              <div className="flex shrink-0 items-center gap-2">
                <span className="text-xs text-slate-500">{a.status}</span>
                {a.status === "NEW" && (
                  <button
                    onClick={() => update.mutate({ id: a.id, status: "ACK" })}
                    className="rounded border border-slate-700 px-2 py-1 text-xs hover:bg-slate-800"
                  >
                    Acquitter
                  </button>
                )}
                {a.status !== "RESOLVED" && (
                  <button
                    onClick={() => update.mutate({ id: a.id, status: "RESOLVED" })}
                    className="rounded border border-slate-700 px-2 py-1 text-xs hover:bg-slate-800"
                  >
                    Résoudre
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
