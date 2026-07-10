// Sprint 1 — static placeholder data only.
// No API calls, no WebSocket. Structured so later sprints can swap
// this module for live data with minimal changes to consuming components.

import {
  HeartPulse,
  Radio,
  Activity,
  AlertTriangle,
  Fuel,
  Wrench,
} from 'lucide-react';

export const kpiData = [
  {
    id: 'fleet-health',
    icon: HeartPulse,
    title: 'Fleet Health',
    value: '96%',
    trend: '+2%',
    trendDirection: 'up',
    context: 'Compared to last week',
    status: 'healthy',
  },
  {
    id: 'vehicles-online',
    icon: Radio,
    title: 'Vehicles Online',
    value: '42/48',
    trend: '+3',
    trendDirection: 'up',
    context: 'Compared to yesterday',
    status: 'info',
  },
  {
    id: 'vehicles-active',
    icon: Activity,
    title: 'Vehicles Active',
    value: '31',
    trend: '-4',
    trendDirection: 'down',
    context: 'Compared to yesterday',
    status: 'info',
  },
  {
    id: 'active-alerts',
    icon: AlertTriangle,
    title: 'Active Alerts',
    value: '5',
    trend: '+1',
    trendDirection: 'up',
    context: 'Compared to last week',
    status: 'warning',
  },
  {
    id: 'fuel-efficiency',
    icon: Fuel,
    title: 'Fuel Efficiency',
    value: '8.4 L/100km',
    trend: '-0.3',
    trendDirection: 'up',
    context: 'Compared to last month',
    status: 'healthy',
  },
  {
    id: 'maintenance-due',
    icon: Wrench,
    title: 'Maintenance Due',
    value: '7',
    trend: '+2',
    trendDirection: 'down',
    context: 'Vehicles need service',
    status: 'maintenance',
  },
];

// Mock rows for the Live Fleet Table. Field names mirror the eventual
// OBD-II/WebSocket payload shape so this can be swapped later.
export const fleetTableData = [
  {
    id: 'VH-1042',
    vehicle: 'Ford Transit · VH-1042',
    driver: 'M. Ahmed',
    status: 'active',
    speed: '62 km/h',
    fuel: '74%',
    health: '96%',
    driverScore: 88,
    alerts: 0,
    lastUpdated: '2s ago',
  },
  {
    id: 'VH-1017',
    vehicle: 'Toyota Hiace · VH-1017',
    driver: 'S. Khan',
    status: 'warning',
    speed: '0 km/h',
    fuel: '22%',
    health: '81%',
    driverScore: 74,
    alerts: 2,
    lastUpdated: '5s ago',
  },
  {
    id: 'VH-0988',
    vehicle: 'Honda Civic · VH-0988',
    driver: 'A. Raza',
    status: 'active',
    speed: '104 km/h',
    fuel: '58%',
    health: '92%',
    driverScore: 91,
    alerts: 0,
    lastUpdated: '1s ago',
  },
  {
    id: 'VH-0954',
    vehicle: 'Isuzu D-Max · VH-0954',
    driver: 'F. Bilal',
    status: 'critical',
    speed: '0 km/h',
    fuel: '11%',
    health: '54%',
    driverScore: 63,
    alerts: 3,
    lastUpdated: '11s ago',
  },
  {
    id: 'VH-0901',
    vehicle: 'Suzuki Bolan · VH-0901',
    driver: 'N. Iqbal',
    status: 'offline',
    speed: '—',
    fuel: '—',
    health: '—',
    driverScore: '—',
    alerts: 0,
    lastUpdated: '14m ago',
  },
  {
    id: 'VH-0876',
    vehicle: 'Ford Transit · VH-0876',
    driver: 'K. Sheikh',
    status: 'active',
    speed: '48 km/h',
    fuel: '65%',
    health: '89%',
    driverScore: 85,
    alerts: 1,
    lastUpdated: '3s ago',
  },
];

// Status → color-token mapping shared by table + badges.
export const statusColorMap = {

    active: "success",

    idle: "warning",

    offline: "critical",

};

export const statusLabelMap = {

    active: "Active",

    idle: "Idle",

    offline: "Offline",

};
