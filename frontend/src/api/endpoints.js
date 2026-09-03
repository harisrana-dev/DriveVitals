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
  analytics: {
    summary: '/analytics/summary',
    fleetTrend: '/analytics/fleet-trend',
    drivers: '/analytics/drivers',
    driverTrend: (id) => `/analytics/drivers/${id}/trend`,
    safetyDistribution: '/analytics/safety-distribution',
    vehicles: '/analytics/vehicles',
    trips: '/analytics/trips',
    events: '/analytics/events',
    eventsTrend: '/analytics/events/trend',
    insights: '/analytics/insights',
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
  auth: {
    signup: '/auth/signup',
    login: '/auth/login',
    logout: '/auth/logout',
    me: '/auth/me',
  },
  settings: {
    all: '/settings',
    category: (cat) => `/settings/${cat}`,
  },
  digitalTwin: {
    status: '/digital-twin/status',
    reset: '/digital-twin/reset',
    drivers: '/digital-twin/drivers',
    driver: (id) => `/digital-twin/drivers/${id}`,
    vehicles: '/digital-twin/vehicles',
    vehicle: (id) => `/digital-twin/vehicles/${id}`,
    routes: '/digital-twin/routes',
    route: (id) => `/digital-twin/routes/${id}`,
    assignments: '/digital-twin/assignments',
    assignment: (id) => `/digital-twin/assignments/${id}`,
    scenarios: '/digital-twin/scenarios',
    scenario: (id) => `/digital-twin/scenarios/${id}`,
    scenarioLaunch: (id) => `/digital-twin/scenarios/${id}/launch`,
    scenarioStop: (id) => `/digital-twin/scenarios/${id}/stop`,
    scenarioActivate: (id) => `/digital-twin/scenarios/${id}/activate`,
    scenarioAssignments: (id) => `/digital-twin/scenarios/${id}/assignments`,
    scenarioRuns: (id) => `/digital-twin/scenarios/${id}/runs`,
  },
};

export { endpoints };
