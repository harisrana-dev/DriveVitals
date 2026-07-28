export const vehicles = [
  { id: 'V-101', name: 'Ford F-150', driver: 'James Mitchell', driverId: 'D-01', status: 'active', speed: 72, rpm: 2100, fuelLevel: 68, coolantTemp: 88, healthScore: 87, healthCategory: 'healthy', odometer: 48230, lastUpdate: 'Just now', alertCount: 1, activeAlert: 'Oil service due' },
  { id: 'V-102', name: 'Chevrolet Silverado', driver: 'Sarah Chen', driverId: 'D-02', status: 'active', speed: 56, rpm: 1800, fuelLevel: 82, coolantTemp: 85, healthScore: 94, healthCategory: 'healthy', odometer: 31450, lastUpdate: 'Just now', alertCount: 0 },
  { id: 'V-103', name: 'RAM 1500', driver: 'David Park', driverId: 'D-03', status: 'warning', speed: 45, rpm: 2400, fuelLevel: 34, coolantTemp: 112, healthScore: 62, healthCategory: 'attention', odometer: 72100, lastUpdate: '2 min ago', alertCount: 2, activeAlert: 'High coolant temperature' },
  { id: 'V-104', name: 'Toyota Tacoma', driver: 'Maria Garcia', driverId: 'D-04', status: 'active', speed: 88, rpm: 2600, fuelLevel: 55, coolantTemp: 90, healthScore: 78, healthCategory: 'monitor', odometer: 56800, lastUpdate: 'Just now', alertCount: 1, activeAlert: 'Brake wear' },
  { id: 'V-105', name: 'Nissan Frontier', driver: 'Robert Kim', driverId: 'D-05', status: 'idle', speed: 0, rpm: 800, fuelLevel: 91, coolantTemp: 82, healthScore: 96, healthCategory: 'healthy', odometer: 12300, lastUpdate: '5 min ago', alertCount: 0 },
  { id: 'V-106', name: 'GMC Sierra', driver: 'Emily Watson', driverId: 'D-06', status: 'active', speed: 65, rpm: 1950, fuelLevel: 73, coolantTemp: 87, healthScore: 91, healthCategory: 'healthy', odometer: 38900, lastUpdate: 'Just now', alertCount: 0 },
  { id: 'V-107', name: 'Ford Ranger', driver: 'Alex Thompson', driverId: 'D-07', status: 'active', speed: 42, rpm: 1600, fuelLevel: 60, coolantTemp: 86, healthScore: 85, healthCategory: 'healthy', odometer: 29100, lastUpdate: 'Just now', alertCount: 0 },
  { id: 'V-108', name: 'Honda Ridgeline', driver: 'Lisa Anderson', driverId: 'D-08', status: 'offline', speed: 0, rpm: 0, fuelLevel: 45, coolantTemp: 0, healthScore: 71, healthCategory: 'monitor', odometer: 61200, lastUpdate: '3 hours ago', alertCount: 1, activeAlert: 'Connectivity lost' },
  { id: 'V-109', name: 'Jeep Gladiator', driver: 'Michael Brown', driverId: 'D-09', status: 'active', speed: 78, rpm: 2200, fuelLevel: 62, coolantTemp: 89, healthScore: 88, healthCategory: 'healthy', odometer: 44600, lastUpdate: 'Just now', alertCount: 0 },
  { id: 'V-110', name: 'Chevrolet Colorado', driver: 'Jennifer Lee', driverId: 'D-10', status: 'idle', speed: 0, rpm: 750, fuelLevel: 78, coolantTemp: 81, healthScore: 92, healthCategory: 'healthy', odometer: 22800, lastUpdate: '8 min ago', alertCount: 0 },
  { id: 'V-111', name: 'Toyota Tundra', driver: 'Chris Martinez', driverId: 'D-11', status: 'warning', speed: 35, rpm: 2500, fuelLevel: 28, coolantTemp: 98, healthScore: 58, healthCategory: 'attention', odometer: 89400, lastUpdate: '1 min ago', alertCount: 3, activeAlert: 'Low fuel + high RPM' },
  { id: 'V-112', name: 'Ford Maverick', driver: 'Amanda White', driverId: 'D-12', status: 'active', speed: 61, rpm: 1750, fuelLevel: 85, coolantTemp: 84, healthScore: 97, healthCategory: 'healthy', odometer: 8900, lastUpdate: 'Just now', alertCount: 0 },
];

export const drivers = [
  { id: 'D-01', name: 'James Mitchell', safetyScore: 88, tripsCompleted: 142, harshBraking: 3, rapidAccel: 2, speedViolations: 1, trend: 'stable' },
  { id: 'D-02', name: 'Sarah Chen', safetyScore: 96, tripsCompleted: 198, harshBraking: 1, rapidAccel: 0, speedViolations: 0, trend: 'improving' },
  { id: 'D-03', name: 'David Park', safetyScore: 72, tripsCompleted: 87, harshBraking: 8, rapidAccel: 5, speedViolations: 3, trend: 'declining' },
  { id: 'D-04', name: 'Maria Garcia', safetyScore: 84, tripsCompleted: 156, harshBraking: 4, rapidAccel: 3, speedViolations: 1, trend: 'stable' },
  { id: 'D-05', name: 'Robert Kim', safetyScore: 95, tripsCompleted: 210, harshBraking: 0, rapidAccel: 1, speedViolations: 0, trend: 'improving' },
  { id: 'D-06', name: 'Emily Watson', safetyScore: 91, tripsCompleted: 175, harshBraking: 2, rapidAccel: 1, speedViolations: 0, trend: 'stable' },
  { id: 'D-07', name: 'Alex Thompson', safetyScore: 78, tripsCompleted: 95, harshBraking: 6, rapidAccel: 4, speedViolations: 2, trend: 'declining' },
  { id: 'D-08', name: 'Lisa Anderson', safetyScore: 82, tripsCompleted: 130, harshBraking: 3, rapidAccel: 2, speedViolations: 1, trend: 'stable' },
  { id: 'D-09', name: 'Michael Brown', safetyScore: 90, tripsCompleted: 168, harshBraking: 2, rapidAccel: 1, speedViolations: 0, trend: 'improving' },
  { id: 'D-10', name: 'Jennifer Lee', safetyScore: 93, tripsCompleted: 201, harshBraking: 1, rapidAccel: 0, speedViolations: 0, trend: 'improving' },
  { id: 'D-11', name: 'Chris Martinez', safetyScore: 69, tripsCompleted: 72, harshBraking: 9, rapidAccel: 7, speedViolations: 4, trend: 'declining' },
  { id: 'D-12', name: 'Amanda White', safetyScore: 97, tripsCompleted: 220, harshBraking: 0, rapidAccel: 0, speedViolations: 0, trend: 'improving' },
];

export const alerts = [
  { id: 'A-01', severity: 'critical', vehicleId: 'V-103', vehicleName: 'RAM 1500', driverId: 'D-03', driverName: 'David Park', title: 'High coolant temperature', description: 'Engine coolant temperature has exceeded safe operating threshold', value: '112\u00b0C', threshold: '105\u00b0C', timestamp: '2 minutes ago', acknowledged: false, actionLabel: 'View Vehicle' },
  { id: 'A-02', severity: 'warning', vehicleId: 'V-101', vehicleName: 'Ford F-150', title: 'Oil service due', description: 'Scheduled oil change overdue based on mileage interval', value: '420 km remaining', timestamp: '15 minutes ago', acknowledged: false, actionLabel: 'Schedule Service' },
  { id: 'A-03', severity: 'warning', vehicleId: 'V-111', vehicleName: 'Toyota Tundra', driverId: 'D-11', driverName: 'Chris Martinez', title: 'Low fuel level', description: 'Fuel tank below 30% capacity', value: '28%', timestamp: '1 minute ago', acknowledged: false, actionLabel: 'View Vehicle' },
  { id: 'A-04', severity: 'critical', vehicleId: 'V-111', vehicleName: 'Toyota Tundra', driverId: 'D-11', driverName: 'Chris Martinez', title: 'Repeated harsh braking', description: '6 harsh braking events detected during current trip', value: '6 events', threshold: '3 events', timestamp: '8 minutes ago', acknowledged: false, actionLabel: 'Review Trip' },
  { id: 'A-05', severity: 'info', vehicleId: 'V-104', vehicleName: 'Toyota Tacoma', title: 'Brake pad wear', description: 'Front brake pads approaching replacement threshold', value: 'Monitor condition', timestamp: '1 hour ago', acknowledged: true, actionLabel: 'View Vehicle' },
  { id: 'A-06', severity: 'warning', vehicleId: 'V-108', vehicleName: 'Honda Ridgeline', driverId: 'D-08', driverName: 'Lisa Anderson', title: 'Connectivity lost', description: 'Vehicle telematics unit offline since last transmission', value: '3 hours', timestamp: '3 hours ago', acknowledged: false, actionLabel: 'View Vehicle' },
];

export const maintenanceItems = [
  { id: 'M-01', vehicleId: 'V-101', type: 'Oil Change', priority: 'upcoming', dueDistance: 420, description: 'Synthetic oil change and filter replacement' },
  { id: 'M-02', vehicleId: 'V-104', type: 'Brake Inspection', priority: 'monitor', dueDate: '2 weeks', description: 'Front brake pad wear approaching limit' },
  { id: 'M-03', vehicleId: 'V-109', type: 'Scheduled Service', priority: 'upcoming', dueDistance: 1200, description: '60,000 km major service interval' },
  { id: 'M-04', vehicleId: 'V-103', type: 'Coolant System', priority: 'critical', description: 'Coolant temperature anomaly requires inspection', dueDistance: 0 },
  { id: 'M-05', vehicleId: 'V-108', type: 'Tire Rotation', priority: 'monitor', dueDistance: 800, description: 'Standard tire rotation and pressure check' },
];

export const dashboardSummary = {
  totalVehicles: 12,
  activeVehicles: 7,
  idleVehicles: 2,
  warningVehicles: 2,
  offlineVehicles: 1,
  fleetHealthScore: 86,
  attentionRequired: 3,
  alertsToday: 6,
};

export const telemetryData = [
  { time: '06:00', fuelEfficiency: 8.2, safetyScore: 88, activeVehicles: 4 },
  { time: '07:00', fuelEfficiency: 7.9, safetyScore: 87, activeVehicles: 8 },
  { time: '08:00', fuelEfficiency: 7.5, safetyScore: 85, activeVehicles: 10 },
  { time: '09:00', fuelEfficiency: 7.8, safetyScore: 86, activeVehicles: 11 },
  { time: '10:00', fuelEfficiency: 8.0, safetyScore: 88, activeVehicles: 11 },
  { time: '11:00', fuelEfficiency: 8.3, safetyScore: 89, activeVehicles: 10 },
  { time: '12:00', fuelEfficiency: 8.1, safetyScore: 88, activeVehicles: 9 },
  { time: '13:00', fuelEfficiency: 7.7, safetyScore: 86, activeVehicles: 10 },
  { time: '14:00', fuelEfficiency: 7.6, safetyScore: 85, activeVehicles: 11 },
  { time: '15:00', fuelEfficiency: 7.9, safetyScore: 87, activeVehicles: 10 },
  { time: '16:00', fuelEfficiency: 8.1, safetyScore: 89, activeVehicles: 9 },
  { time: '17:00', fuelEfficiency: 8.4, safetyScore: 90, activeVehicles: 7 },
];
