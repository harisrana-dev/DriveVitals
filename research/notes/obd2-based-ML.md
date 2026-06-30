# Research Notes 02

## Paper Information

- **Title:** A Review of OBD-II-Based Machine Learning Applications for Sustainable, Efficient, Secure, and Safe Vehicle Driving
- **Authors:** Emmanouel T. Michailidis, Antigoni Panagiotopoulou, Andreas Papadakis
- **Year:** 2025
- **Paper Type:** Systematic Literature Review

---

# 1. Research Problem

Although OBD-II was originally designed for emissions monitoring and vehicle diagnostics, recent research has expanded its use into Intelligent Transportation Systems (ITS), enabling applications such as:

- Driver Behavior Analysis
- Eco-Driving
- Fuel Consumption Estimation
- Predictive Maintenance
- Vehicle Health Monitoring
- Driver Identification
- Drowsiness Detection

However, challenges remain regarding interoperability between vehicle manufacturers, protocol compatibility, proprietary PIDs, and data quality.

---

# 2. Research Objective

The paper reviews modern machine learning applications built upon OBD-II telemetry.

It investigates:

- Sustainable driving
- Fuel optimization
- Driver behavior analysis
- Predictive maintenance
- Vehicle safety
- Vehicle security
- Machine learning techniques
- Open research challenges

---

# 3. Evolution of OBD-II

Originally designed for:

- Emissions monitoring
- Fault diagnosis
- Diagnostic Trouble Codes (DTCs)

Current research extends OBD-II into:

- Eco-driving systems
- Predictive maintenance
- Driver profiling
- Fleet analytics
- AI-based decision systems
- Vehicle health monitoring

---

# 4. Common OBD-II Telemetry Parameters

Frequently collected parameters include:

- Engine RPM
- Vehicle Speed
- Engine Load
- Throttle Position
- Mass Air Flow (MAF)
- Coolant Temperature
- Ignition Timing
- Battery Voltage
- Steering Angle
- Brake Pressure
- Engine Torque
- Gear Position
- GPS Location

These parameters form the foundation of most machine learning models.

---

# 5. Machine Learning Applications

The survey identifies several major application areas.

## Driver Behavior Analysis

Used for:

- Aggressive driving detection
- Driving style recognition
- Driver profiling
- Risk assessment

Common inputs:

- Speed
- RPM
- Throttle Position
- Acceleration
- Brake Pressure

---

## Fuel Consumption Estimation

OBD-II telemetry is widely used for estimating fuel consumption.

Frequently used features:

- RPM
- Engine Load
- MAF
- Speed
- Throttle Position
- Ignition Timing

---

## Predictive Maintenance

Machine learning models analyze historical telemetry to predict:

- Component failures
- Maintenance schedules
- Engine anomalies
- Vehicle health degradation

---

## Driver Drowsiness Detection

Hybrid approaches combine:

- OBD-II telemetry
- Camera data
- Facial analysis

Example telemetry:

- RPM
- Vehicle Speed
- Steering Torque
- Throttle Position

---

## Driver Identification

Machine learning models identify drivers using:

- Throttle usage
- Brake patterns
- Gear shifting
- Speed profiles

---

# 6. Representative Research Studies

## Eco-Driving System

Vehicle Models:

- Mazda 3
- Mitsubishi Lancer
- Toyota Vios

Collected parameters:

- RPM
- Speed
- Engine Load
- MAF
- Coolant Temperature
- Ignition Timing
- Throttle Position
- Battery Voltage

Models evaluated:

- Feed Forward Backpropagation (FFB)
- RNN
- Elman Neural Network

Best performer:

- Elman Neural Network

---

## Fuel Consumption Estimation

Algorithms:

- Random Forest
- Artificial Neural Network (ANN)

Observation:

Random Forest consistently outperformed ANN for real-time fuel estimation.

---

## Heavy Duty Truck Fuel Prediction

Models:

- VSP
- VT-Micro
- Engine Output Power
- ANN
- LSTM-Convolution Network

Vehicle weight significantly improves prediction accuracy.

---

## Driver Drowsiness Detection

Combined:

- OBD-II telemetry
- Facial video

Telemetry included:

- Speed
- RPM
- Throttle Position
- Steering Torque

---

## Driving Style Recognition

Algorithm:

- Semi-Supervised Gaussian Mixture Model (GMM)

Performance:

- Accuracy: 92%
- Macro Precision: 92.2%
- F1 Score: 92.15%

---

## Driving Behavior Classification

Dataset:

- 94,380 samples
- 26 hours
- 10 drivers
- 51 telemetry parameters
- 1-second sampling interval

Algorithms:

- CatBoost
- AdaBoost
- LightGBM
- Gradient Boosting
- XGBoost

Best performer:

- LightGBM

Accuracy:

99.68%

---

# 7. Machine Learning Algorithms

Frequently used algorithms include:

- Random Forest
- Support Vector Machine (SVM)
- LightGBM
- XGBoost
- CatBoost
- Gradient Boosting
- Gaussian Mixture Model (GMM)
- Artificial Neural Networks
- RNN
- LSTM
- Elman Neural Networks

---

# 8. Key Observations

- OBD-II has evolved beyond diagnostics into an important source of AI-ready vehicle telemetry.
- Random Forest performs well in real-time applications due to its accuracy and interpretability.
- LSTM models perform better for sequential driving behavior but require larger datasets and more computational resources.
- Edge AI enables real-time inference without relying on cloud connectivity.
- Hybrid systems combining OBD-II with cameras outperform single-modality systems.

---

# 9. Challenges Identified

Several limitations remain in current OBD-II-based systems.

## Hardware Compatibility

- Different CAN protocols
- Legacy vehicle support
- Electric vehicle compatibility

---

## Manufacturer Differences

- Proprietary PIDs
- Different scaling factors
- Different byte formats

These differences reduce model portability across vehicle manufacturers.

---

## Sensor Quality

Some sensors introduce measurement errors.

Example:

- NOx sensors may exhibit error rates exceeding 40%.

---

## Road Perception

OBD-II only measures internal vehicle telemetry.

It cannot directly perceive:

- Road conditions
- Lane markings
- Traffic signs
- Pedestrians

Additional sensors (camera, radar, LiDAR) are required.

---

# 10. Insights for DriveVitals

This paper strongly validates the proposed DriveVitals architecture.

DriveVitals should focus on:

- Real-time telemetry collection
- Driver behavior analysis
- Vehicle health monitoring
- Fuel efficiency estimation
- Historical telemetry storage
- Edge-based analytics
- Future AI integration

Future versions can integrate:

- Computer Vision
- Driver Monitoring Systems
- Predictive Maintenance
- Fleet Intelligence

---

# 11. Research Gaps

Potential opportunities include:

- Unified support across different vehicle manufacturers.
- Better handling of proprietary PIDs.
- Combining OBD-II telemetry with Computer Vision.
- Explainable AI (XAI) for driver behavior scoring.
- Lightweight ML models suitable for embedded edge devices.
- More generalized predictive maintenance systems.

---

# 12. Action Items for DriveVitals

Based on this paper:

- Prioritize standardized OBD-II PIDs.
- Design modular telemetry collection.
- Store historical telemetry for AI training.
- Begin with rule-based analytics before introducing machine learning.
- Build the backend to support future edge AI deployment.
- Design the dashboard around high-value telemetry signals.

---

# 13. Personal Reflection

This paper significantly strengthened the technical direction of DriveVitals. It confirms that OBD-II is no longer used solely for diagnostics but has become a valuable source of telemetry for machine learning applications such as eco-driving, driver behavior analysis, predictive maintenance, and vehicle health monitoring. The survey also highlights important limitations including protocol interoperability, manufacturer-specific PIDs, and the inability of OBD-II to perceive the external driving environment. These findings support DriveVitals' modular design philosophy, where rule-based analytics provide an initial solution while future versions integrate machine learning and computer vision for more comprehensive driver and vehicle intelligence.