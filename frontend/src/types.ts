export interface Role {
  id: number;
  name: string;
  description?: string | null;
}

export interface User {
  id: number;
  username: string;
  email?: string | null;
  full_name?: string | null;
  is_active: boolean;
  role: Role;
  created_at: string;
}

export interface Infrastructure {
  id: number;
  name: string;
  description?: string | null;
  location?: string | null;
  environment: string;
  status: string;
  provider?: string | null;
  api_endpoint?: string | null;
  created_at: string;
  updated_at: string;
}

export interface NodeRow {
  id: number;
  name: string;
  status: string;
  ip?: string | null;
  cpu_usage: number;
  ram_usage: number;
  disk_usage: number;
  uptime_seconds: number;
  kernel?: string | null;
  version?: string | null;
  load?: string | null;
  updated_at: string;
}

export interface VMRow {
  id: number;
  node_id: number;
  node_name?: string | null;
  vmid: number;
  name: string;
  status: string;
  cpu_usage: number;
  ram_mb: number;
  disk_gb: number;
  ip?: string | null;
  uptime_seconds: number;
}

export interface ContainerRow extends Omit<VMRow, "vmid"> {
  ctid: number;
}

export interface StorageRow {
  id: number;
  node_id: number;
  name: string;
  type?: string | null;
  total_gb: number;
  used_gb: number;
  free_gb: number;
  usage_percent: number;
  status: string;
}

export interface BackupJob {
  id: number;
  name: string;
  source?: string | null;
  target?: string | null;
  schedule?: string | null;
  retention?: string | null;
  backup_type?: string | null;
  environment?: string | null;
  server?: string | null;
  last_run_at?: string | null;
  next_run_at?: string | null;
  duration_seconds: number;
  size_gb: number;
  status: string;
}

export interface BackupHistoryRow {
  id: number;
  job_name?: string | null;
  server?: string | null;
  vm?: string | null;
  started_at?: string | null;
  ended_at?: string | null;
  duration_seconds: number;
  backup_size_gb: number;
  transferred_gb: number;
  status: string;
  error?: string | null;
}

export interface BackupRepository {
  id: number;
  name: string;
  type?: string | null;
  total_capacity_gb: number;
  used_gb: number;
  free_gb: number;
  usage_percent: number;
  status: string;
  last_backup_at?: string | null;
}

export interface VeeamServer {
  id: number;
  name: string;
  hostname: string;
  api_url: string;
  port: number;
  username?: string | null;
  tls_verify: boolean;
  enabled: boolean;
  last_sync_at?: string | null;
}

export interface VeeamJob {
  id: number;
  name: string;
  type?: string | null;
  status: string;
  last_run_at?: string | null;
  next_run_at?: string | null;
  duration_seconds: number;
  transferred_gb: number;
  backup_size_gb: number;
}

export interface Alert {
  id: number;
  alert_type: string;
  severity: string;
  title: string;
  description?: string | null;
  source?: string | null;
  resource?: string | null;
  status: string;
  timestamp: string;
}

export interface AuditEntry {
  id: number;
  username: string;
  action: string;
  resource?: string | null;
  resource_id?: string | null;
  ip_address?: string | null;
  result: string;
  timestamp: string;
}

export interface DashboardSummary {
  datacenters: number;
  nodes: number;
  vms: number;
  containers: number;
  veeam_servers: number;
  backup_repositories: number;
  nodes_online: number;
  nodes_offline: number;
  vms_running: number;
  vms_stopped: number;
  storage_warnings: number;
  backup_failures: number;
  backup_warnings: number;
  last_successful_backup?: string | null;
  running_backups: number;
  recent_activity: { user: string; action: string; resource?: string | null; at: string }[];
}

export interface ProxmoxServer {
  id: number;
  name: string;
  host: string;
  api_url: string;
  port: number;
  token_id: string;
  tls_verify: boolean;
  enabled: boolean;
  last_sync_at?: string | null;
}
