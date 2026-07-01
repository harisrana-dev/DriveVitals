# Constraints

The DriveVitals system operates under the following constraints:

- Limited and inconsistent PID availability across different vehicle manufacturers.
- Dependency on third-party ELM327 adapters, which may vary in quality and latency.
- Real-time data accuracy is subject to ECU response limitations.
- Fuel consumption values are estimated and not directly measured in most vehicles.
- Continuous high-frequency polling may be restricted by some ECUs or adapters.
- Not all vehicles expose advanced diagnostic parameters such as emissions or torque data.
- Bluetooth/Wi-Fi communication may introduce latency or packet loss.