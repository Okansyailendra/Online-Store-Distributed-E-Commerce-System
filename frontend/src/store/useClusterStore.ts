import { create } from "zustand";

export interface ClusterNode {
  id: string;
  name: string;
  role: "COORDINATOR" | "FOLLOWER";
  host: string;
  port: number;
  protocol: string;
  online: boolean;
}

export interface FailoverAlert {
  show: boolean;
  service: string;
  message: string;
  timestamp: number;
}

interface ClusterStore {
  nodes: ClusterNode[];
  clusterHealthy: boolean;
  failoverAlert: FailoverAlert | null;
  isLoading: boolean;
  fetchClusterStatus: () => Promise<void>;
  triggerFailoverAlert: (service: string, message: string) => void;
  dismissFailoverAlert: () => void;
}

export const useClusterStore = create<ClusterStore>((set) => ({
  nodes: [],
  clusterHealthy: true,
  failoverAlert: null,
  isLoading: false,

  fetchClusterStatus: async () => {
    try {
      const res = await fetch("/api/proxy/cluster/status");
      const json = await res.json();
      if (json.success) {
        set({
          nodes: json.nodes || [],
          clusterHealthy: json.cluster_healthy,
        });
      }
    } catch (e) {
      console.error("Gagal mengambil status cluster:", e);
    }
  },

  triggerFailoverAlert: (service, message) => {
    set({
      failoverAlert: {
        show: true,
        service,
        message,
        timestamp: Date.now(),
      },
    });
  },

  dismissFailoverAlert: () => {
    set({ failoverAlert: null });
  },
}));
