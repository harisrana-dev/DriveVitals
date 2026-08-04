const endpoints = {
  fleet: {
    list: '/vehicles',
    vehicle: (id) => `/vehicles/${id}`,
    health: (id) => `/vehicles/${id}/health`,
  },
  alerts: {
    list: '/alerts',
    acknowledge: (id) => `/alerts/${id}/acknowledge`,
  },
  maintenance: {
    list: '/maintenance',
    item: (id) => `/maintenance/${id}`,
  },
  trips: {
    list: '/trips',
  },
  drivers: {
    list: '/drivers',
    driver: (id) => `/drivers/${id}`,
  },
  summary: {
    fleet: '/summary',
    driver: '/driver-summary',
    vehicle: '/vehicle-summary',
  },
  health: {
    check: '/health',
  },
};

export { endpoints };
