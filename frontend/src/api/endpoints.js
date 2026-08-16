const endpoints = {
  fleet: {
    list: '/vehicles',
    vehicle: (id) => `/vehicles/${id}`,
    health: (id) => `/vehicles/${id}/health`,
  },
  vehicleHealth: {
    list: '/vehicle-health',
    item: (id) => `/vehicle-health/${id}`,
    config: '/vehicle-health/config',
  },
  alerts: {
    list: '/alerts',
    vehicle: (id) => `/alerts/${id}`,
    acknowledge: (id) => `/alerts/${id}/acknowledge`,
    resolve: (id) => `/alerts/${id}/resolve`,
  },
  maintenance: {
    list: '/maintenance',
    item: (id) => `/maintenance/${id}`,
    complete: (id) => `/maintenance/${id}/complete`,
  },
  trips: {
    list: '/trips',
    item: (id) => `/trips/${id}`,
    aborted: '/trips/aborted',
  },
  drivers: {
    list: '/drivers',
    driver: (id) => `/drivers/${id}`,
  },
  driverStatistics: {
    list: '/driver-statistics',
    driver: (id) => `/driver-statistics/${id}`,
  },
  telemetry: {
    list: '/telemetry',
    vehicle: (id) => `/telemetry/${id}`,
  },
  summary: {
    fleet: '/summary',
    vehicle: '/vehicle-summary',
  },
  health: {
    check: '/system/health',
    status: '/system/status',
    version: '/system/version',
  },
};

export { endpoints };
