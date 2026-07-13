# DriveVitals Database Design Documentation

## 1. Overview

The DriveVitals platform requires a persistent data storage layer to transform real-time vehicle telemetry into historical fleet intelligence.

Unlike a simple telemetry dashboard, DriveVitals stores, processes, and analyzes vehicle data over time to generate meaningful operational insights.

The database layer stores:

- Vehicle information
- Raw ECU/OBD-II telemetry data
- Processed fuel efficiency analytics
- Driver behavior events
- Trip summaries
- Vehicle health analysis
- Fleet intelligence insights
- Historical performance trends

The database enables advanced fleet management capabilities including:

- Real-time fleet monitoring
- Fuel efficiency analysis
- Driver performance evaluation
- Vehicle health monitoring
- Predictive maintenance research
- Historical reporting
- Machine learning-based anomaly detection

---

# 2. Database Architecture

DriveVitals follows a layered data architecture:

```
Vehicle Simulator / OBD-II Source
              |
              |
              v
      Telemetry Ingestion Layer
              |
              |
              v
        PostgreSQL Database
              |
              |
              v
        Analytics Engine
              |
              |
              v
       Fleet Intelligence Layer
              |
              |
              v
        Dashboard Insights
```

The database acts as the historical memory of the fleet by storing both raw vehicle signals and processed intelligence.

---

# 3. Database Technology

## Database

```
PostgreSQL
```

PostgreSQL is selected as the primary database because DriveVitals requires:

- High-volume telemetry storage
- Time-based historical queries
- Concurrent data processing
- Scalable relational storage
- Cloud deployment compatibility


## ORM

```
SQLAlchemy
```

SQLAlchemy provides:

- Database abstraction
- Object relational mapping
- Clean model architecture
- Easy migration between environments


## Migration Tool

```
Alembic
```

Alembic manages:

- Database schema changes
- Version-controlled migrations
- Production database updates

---

# 4. Database Design Principles

The database design follows these principles:

## Separation of Raw and Processed Data

Raw telemetry is stored independently from analytics results.

Example:

```
Telemetry Data

speed
rpm
engine_load
fuel_rate


        |
        v


Analytics Processing


        |
        v


Fuel Efficiency
Vehicle Health
Driver Score
```

---

## Historical Intelligence

All analytics results are timestamped to support:

- Daily comparisons
- Weekly trends
- Monthly reports
- Performance analysis

---

## Future Hardware Compatibility

The database design supports multiple telemetry sources:

```
Simulator
    |
    |
OBD-II Adapter
    |
    |
CAN Bus Integration
```

The backend remains independent of the data source.

---

# 5. Database Entities

The initial database consists of the following entities:

| Entity | Purpose |
|-|-|
| Vehicle | Stores registered fleet vehicles |
| Telemetry | Stores raw vehicle sensor data |
| Fuel Efficiency | Stores calculated fuel economy results |
| Driver Events | Stores detected driving behavior |
| Trips | Stores completed journey summaries |
| Vehicle Health | Stores vehicle condition analysis |
| Fleet Insights | Stores generated recommendations |

---

# 6. Entity Relationship Overview

```
                         Vehicle
                            |
                            |
        -----------------------------------------
        |                  |                    |
        v                  v                    v

   Telemetry       Fuel Efficiency       Vehicle Health


        |
        |
        v

      Trips

        |
        |
        v

 Driver Behaviour Events


        |
        |
        v

 Fleet Intelligence Insights
```

---

# 7. Database Tables

---

# 7.1 Vehicle Table

Stores registered fleet vehicles.

Table:

```
vehicles
```

## Columns

| Column | Type | Description |
|-|-|-|
| id | Integer | Primary key |
| vehicle_id | String | Unique vehicle identifier |
| make | String | Manufacturer |
| model | String | Vehicle model |
| year | Integer | Manufacturing year |
| created_at | Timestamp | Registration date |

Example:

```json
{
 "vehicle_id":"V001",
 "make":"Toyota",
 "model":"Corolla",
 "year":2022
}
```

---

# 7.2 Telemetry Table

Stores raw vehicle signals received from OBD-II or simulator.

This table represents the vehicle's real-time state history.

Table:

```
telemetry
```

## Columns

| Column | Type | Description |
|-|-|-|
| id | Integer | Primary key |
| vehicle_id | String | Vehicle reference |
| timestamp | Timestamp | Data capture time |
| speed_kmh | Float | Vehicle speed |
| rpm | Float | Engine RPM |
| engine_load | Float | Engine load percentage |
| coolant_temp | Float | Coolant temperature |
| throttle_position | Float | Throttle position |
| fuel_rate_lph | Float | Fuel consumption rate |
| maf | Float | Mass airflow |

Example:

```json
{
 "vehicle_id":"V001",
 "speed_kmh":65,
 "rpm":2400,
 "engine_load":45,
 "coolant_temp":88
}
```

---

# 7.3 Fuel Efficiency Table

Stores processed fuel economy analytics.

The primary business metric is:

```
km/L
```

The system converts raw fuel consumption data into fleet-friendly efficiency measurements.

Table:

```
fuel_efficiency
```

## Columns

| Column | Type | Description |
|-|-|-|
| id | Integer | Primary key |
| vehicle_id | String | Vehicle reference |
| timestamp | Timestamp | Calculation time |
| km_per_liter | Float | Fuel efficiency |
| rating | String | Efficiency rating |

Example:

```json
{
 "vehicle_id":"V001",
 "km_per_liter":14.8,
 "rating":"good"
}
```

---

# 7.4 Driver Events Table

Stores detected driver behavior events.

Table:

```
driver_events
```

## Columns

| Column | Type | Description |
|-|-|-|
| id | Integer | Primary key |
| vehicle_id | String | Vehicle reference |
| timestamp | Timestamp | Event time |
| event_type | String | Event category |
| severity | String | Severity level |
| value | Float | Event measurement |

Supported events:

```
harsh_acceleration
harsh_braking
overspeeding
excessive_idling
aggressive_driving
```

Example:

```json
{
 "event_type":"harsh_acceleration",
 "severity":"medium"
}
```

---

# 7.5 Trips Table

Stores completed trip summaries.

Table:

```
trips
```

## Columns

| Column | Type | Description |
|-|-|-|
| id | Integer | Primary key |
| vehicle_id | String | Vehicle reference |
| start_time | Timestamp | Trip start |
| end_time | Timestamp | Trip end |
| distance_km | Float | Distance travelled |
| fuel_consumed | Float | Fuel consumed |
| average_efficiency | Float | Trip km/L |
| driver_score | Float | Driving score |

Example:

```json
{
 "distance_km":24.5,
 "average_efficiency":13.8,
 "driver_score":88
}
```

---

# 7.6 Vehicle Health Table

Stores vehicle condition analysis results.

Table:

```
vehicle_health
```

## Columns

| Column | Type | Description |
|-|-|-|
| id | Integer | Primary key |
| vehicle_id | String | Vehicle reference |
| timestamp | Timestamp | Analysis time |
| health_score | Float | Overall health score |
| status | String | Health status |
| issues | JSON | Detected problems |

Example:

```json
{
 "health_score":82,
 "status":"attention",
 "issues":[
    "high engine load"
 ]
}
```

---

# 7.7 Fleet Insights Table

Stores generated fleet intelligence recommendations.

Table:

```
fleet_insights
```

## Columns

| Column | Type | Description |
|-|-|-|
| id | Integer | Primary key |
| vehicle_id | String | Vehicle reference |
| timestamp | Timestamp | Insight generation time |
| category | String | Insight category |
| message | String | Generated insight |
| recommendation | String | Recommended action |

Example:

```json
{
 "category":"fuel",
 "message":"Fuel efficiency decreased by 15%",
 "recommendation":"Review driving behaviour"
}
```

---

# 8. Data Processing Flow

Example fuel efficiency pipeline:

```
Vehicle Telemetry

speed
rpm
fuel_rate


        |
        v


Fuel Efficiency Analyzer


        |
        v


km/L Calculation


        |
        v


fuel_efficiency table


        |
        v


Trend Analysis


        |
        v


Fleet Insight Generation


        |
        v


Dashboard Visualization
```

---

# 9. Future Database Extensions

Future versions may include:

- Users
- Fleet organizations
- Vehicle maintenance records
- GPS tracking history
- Diagnostic trouble codes (DTC)
- Service history
- Machine learning prediction results
- Driver profiles

---

# 10. Design Goals

The DriveVitals database prioritizes:

- Scalability for fleet-level telemetry
- Separation of raw and processed information
- Historical analytics capability
- Real-time and batch processing support
- Machine learning integration
- Compatibility with real OBD-II/CAN data sources

---

# Conclusion

The DriveVitals database provides the foundation for transforming raw automotive telemetry into an intelligent fleet management platform.

By combining PostgreSQL storage, structured analytics data, and historical performance tracking, DriveVitals can generate actionable insights for fuel optimization, driver safety, and predictive vehicle maintenance.