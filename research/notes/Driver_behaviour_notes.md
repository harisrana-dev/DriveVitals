```md
# Research Notes 01

## Paper Information

- **Title:** Driver Behavior Classification: A Systematic Literature Review
- **Authors:** Soukaina Bouhsissin, Nawal Sael, Faouzia Benabbou
- **Year:** 2023
- **Paper Type:** Systematic Literature Review

---

# 1. Research Problem

Road traffic accidents remain one of the leading causes of fatalities worldwide. Unsafe driving behaviors such as aggressive acceleration, harsh braking, lane deviation, and driver fatigue contribute significantly to these accidents. Numerous intelligent transportation systems have been proposed to automatically classify driver behavior using different sensors and machine learning techniques.

---

# 2. Research Objective

This survey aims to analyze and compare existing driver behavior classification research by studying:

- Common data sources
- Sensors used
- Public datasets
- Machine Learning techniques
- Deep Learning techniques
- Driver behavior categories
- Current research trends and limitations

---

# 3. Driver Behaviors Studied

The literature focuses on classifying:

- Aggressive Driving
- Normal Driving
- Abnormal Driving
- Careful Driving
- Drowsy Driving
- Driver Skill Level
- Lane Deviation
- Vehicle Stopping Events

---

# 4. Data Sources & Sensors

## Common Data Sources

| Source | Approximate Usage |
|----------|------------------|
| Driving Simulator | ~25% |
| Camera | ~17% |
| OBD-II Scanner | ~2% |

## Frequently Used Sensors

- GPS
- Accelerometer
- Gyroscope
- Cameras
- ADAS Sensors
- OBD-II Scanner
- Driving Simulator

---

# 5. Common Vehicle Features

The most frequently used features include:

- Vehicle Speed
- Acceleration
- Deceleration
- GPS Trajectory
- Vehicle Motion

---

# 6. Popular Public Datasets

- SHRP2
- UAH DriveSet

These datasets are commonly used for training and evaluating driver behavior classification models.

---

# 7. Machine Learning Algorithms

Frequently used algorithms include:

- Support Vector Machine (SVM)
- Random Forest
- K-Nearest Neighbors (KNN)
- Bayesian Classification
- Logistic Regression
- K-Means Clustering

Machine Learning methods accounted for approximately **60%** of the reviewed studies.

---

# 8. Deep Learning Algorithms

Frequently used architectures include:

- LSTM
- GRU
- CNN
- RNN

Deep Learning methods accounted for approximately **33%** of the reviewed studies.

---

# 9. Representative Results

| Algorithm | Application | Performance |
|------------|-------------|-------------|
| Random Forest | Driver Behavior Classification | ~96% Accuracy |
| GRU | Aggressive Driving Recognition | ~95% Accuracy |
| Bayesian Classification | Smartphone Driver Recognition | ~93.3% Accuracy |
| SVM | Driver Skill Classification | ~95.7% Accuracy |
| KNN | Smartphone Driver Classification | ~78% Accuracy |

---

# 10. Key Observations

- Vehicle speed, acceleration, and deceleration are the most commonly used features.
- Smartphone sensors are widely adopted because they are inexpensive and easy to deploy.
- Driving simulators remain the most popular data source for academic research.
- OBD-II-based research is comparatively limited.
- SVM is the most commonly used Machine Learning algorithm.
- GRU and LSTM are widely used for sequential driving behavior analysis.

---

# 11. Limitations Mentioned by the Authors

- Only papers published between 2015–2022 were reviewed.
- Only Scopus-indexed journals and conferences were considered.
- The survey primarily focuses on driver behavior classification rather than broader vehicle diagnostics or predictive maintenance.

---

# 12. Insights for DriveVitals

This paper provides several important insights for DriveVitals:

## System Design

DriveVitals should combine multiple capabilities instead of focusing solely on driver behavior:

- Driver Behavior Analysis
- Vehicle Health Monitoring
- Fuel Efficiency Estimation
- Predictive Maintenance
- Real-Time Dashboard
- Fleet Analytics

---

## Telemetry Selection

Besides speed and acceleration, DriveVitals should collect ECU telemetry such as:

- Engine RPM
- Engine Load
- Throttle Position
- Mass Air Flow (MAF)
- Fuel Trim
- Coolant Temperature
- Battery Voltage
- Oxygen Sensor Values
- Air-Fuel Ratio

These parameters can improve both driver behavior analysis and vehicle health monitoring.

---

## Future AI Models

Potential algorithms for future implementation include:

- Random Forest
- Support Vector Machine (SVM)
- LSTM
- GRU

---

# 13. Research Gaps

Potential research gaps identified from this survey:

- Limited research utilizing OBD-II telemetry.
- Most studies focus only on driver behavior.
- Few systems integrate vehicle diagnostics with driver analytics.
- Limited work on combining fleet monitoring with individual vehicle monitoring.
- Predictive maintenance is less explored in conjunction with driver behavior analysis.

---

# 14. Action Items for DriveVitals

Based on this paper:

- Study OBD-II architecture and supported PIDs.
- Identify important ECU parameters for behavior analysis.
- Design rule-based driver scoring logic.
- Build a real-time telemetry dashboard.
- Investigate AI models after collecting sufficient telemetry data.

---

# 15. Personal Reflection

This paper provided a comprehensive overview of the driver behavior classification domain. It highlighted the dominant sensors, datasets, algorithms, and current research trends. One particularly interesting observation is the relatively small number of OBD-II-based studies, suggesting an opportunity to explore richer ECU telemetry. The findings reinforce the decision to develop DriveVitals as a modular platform combining driver behavior analysis, vehicle health monitoring, fuel efficiency estimation, and future AI-based predictive maintenance.
```
