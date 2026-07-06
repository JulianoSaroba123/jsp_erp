export const queryKeys = {
  auth: {
    me: ['auth', 'me'] as const,
  },
  customers: {
    all: ['customers'] as const,
    detail: (id: string) => ['customers', id] as const,
  },
  financial: {
    all: ['financial'] as const,
    detail: (id: string) => ['financial', id] as const,
  },
  orders: {
    all: ['orders'] as const,
    detail: (id: string) => ['orders', id] as const,
  },
  products: {
    all: ['products'] as const,
    detail: (id: string) => ['products', id] as const,
  },
  proposals: {
    all: ['proposals'] as const,
    detail: (id: string) => ['proposal', id] as const,
  },
  serviceOrders: {
    all: ['service-orders'] as const,
    detail: (id: string) => ['service-order', id] as const,
  },
  settings: {
    all: ['settings'] as const,
  },
  suppliers: {
    all: ['suppliers'] as const,
    detail: (id: string) => ['supplier', id] as const,
    stats: ['suppliers-stats'] as const,
  },
};
