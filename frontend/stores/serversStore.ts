'use client'

import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface ServersState {
  servers: string[];
  selectedServer: string | null;
  setServers: (servers: string[]) => void;
  selectServer: (server: string | null) => void;
}

export const useServersStore = create<ServersState>()(
  persist(
    (set) => ({
      servers: ['Alpha-1', 'Alpha-2'],
      selectedServer: null,
      setServers: (servers) => set({ servers }),
      selectServer: (server) => set({ selectedServer: server }),
    }),
    {
      name: 'ashes-servers-storage',
    }
  )
)
