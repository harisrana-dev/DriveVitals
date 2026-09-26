/**
 * Fleet create-payload builders for the Digital Twin Lab.
 *
 * These mirror the required fields of the backend create schemas
 * (DriverCreate / VehicleCreate / RouteCreate in
 * backend/api/v1/schemas/digital_twin.py). Every field produced here is
 * mandatory server-side: omitting one returns a 422 whose `detail` is an
 * array rather than a string, which is why the shapes are unit tested.
 *
 * Kept out of DigitalTwinLab.jsx so that page only exports components.
 */

const CURRENT_YEAR = new Date().getFullYear();

const EMPTY_DRIVER_FORM = {
  driver_id: '',
  first_name: '',
  last_name: '',
  license_number: '',
  behavior_profile: 'eco',
};

const EMPTY_VEHICLE_FORM = {
  vehicle_id: '',
  manufacturer: '',
  model: '',
  registration_number: '',
  vin: '',
  year: '',
};

const EMPTY_ROUTE_FORM = {
  route_id: '',
  name: '',
  origin: '',
  destination: '',
  estimated_distance_km: 10,
};

function text(value) {
  return typeof value === 'string' ? value.trim() : '';
}

function buildDriverPayload(form) {
  return {
    driver_id: text(form.driver_id) || null,
    first_name: text(form.first_name),
    last_name: text(form.last_name),
    license_number: text(form.license_number),
    behavior_profile: form.behavior_profile,
  };
}

function buildVehiclePayload(form) {
  return {
    vehicle_id: text(form.vehicle_id) || null,
    manufacturer: text(form.manufacturer),
    model: text(form.model),
    registration_number: text(form.registration_number),
    vin: text(form.vin),
    year: parseInt(form.year, 10) || CURRENT_YEAR,
  };
}

function buildRoutePayload(form) {
  return {
    route_id: text(form.route_id) || null,
    name: text(form.name),
    origin: text(form.origin),
    destination: text(form.destination),
    estimated_distance_km: parseFloat(form.estimated_distance_km) || 0,
  };
}

export {
  buildDriverPayload,
  buildVehiclePayload,
  buildRoutePayload,
  CURRENT_YEAR,
  EMPTY_DRIVER_FORM,
  EMPTY_VEHICLE_FORM,
  EMPTY_ROUTE_FORM,
};
