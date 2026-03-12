# Section X: Test Report

## 1. What Has Been Tested

The following sub-systems and classes were isolated for **unit testing** and **integration testing**:

**1. `VehicleProfileBuilder` (Unit & Integration)**
*   **Item:** `build_from_dataset()` method, which maps preprocessing data into a calibrated `VehicleProfile`.
*   **Equivalence Classes:** Valid fully populated pandas dataframes, empty datasets, and dataframes missing strictly required baseline columns (`RPM`, `Speed`).
*   **Test Oracle:** The architectural design specification. The expected outputs are predictable calculated physics properties (e.g., dynamic weight = base weight + (passenger count × 75kg) + cargo) and correct boolean/type evaluation, verifying standard API fallback data is accurately triggered. 

**2. `FuelEstimator` (Unit)**
*   **Item:** `calculate_trip_fuel_consumption()` static method, which aggregates sequential telemetry to yield an L/100km efficiency metric. 
*   **Equivalence Classes:** Active moving data (Speed > 0, MAF > 0), stationary data (0 distance), and incomplete sensor arrays (Missing MAF/Speed columns).
*   **Test Oracle:** Mathematical correctness against standard stoichiometric formulas and design specs (e.g., distance = 0 must logically reject an L/100km division output returning `NaN`).

---

## 2. Test Cases

### 2.1 Backend Unit Testing: Digital Twin Profiling

| Test Case ID | `profile_unit_01` |
| :--- | :--- |
| **Description of test** | Application successfully builds a calibrated `VehicleProfile` from valid data |
| **Related requirement document details** | Feature 3: Digital Twin Calibration |
| **Pre-requisites for test** | Telematics pandas dataframe parsed; mock `VehicleSpecResolver` available |
| **Test procedure** | 1. Initialize `VehicleProfileBuilder`<br>2. Pass populated `ProcessedDataset` mapping 2 passengers and 50kg cargo.<br>3. System builds and returns Profile object. |
| **Test material used** | Mock typical OBD-II `.csv` telemetry DataFrame (containing `RPM`, `Speed`). |
| **Expected result (test oracle)** | System successfully generates a profile with `dynamic_payload_kg` precisely measuring `200.0` (2x75kg + 50kg cargo). |
| **Comments** | Tests dynamic payload evaluation logic. |
| **Created by** | Othman |
| **Test environment(s)** | Python 3.10+, `.venv` MacOS |

| Test Case ID | `profile_unit_02` |
| :--- | :--- |
| **Description of test** | Application accurately rejects an empty dataset during calibration |
| **Related requirement document details** | Feature 3 Error Handling |
| **Pre-requisites for test** | System active, receiving pipeline traffic |
| **Test procedure** | 1. Initialize `VehicleProfileBuilder`<br>2. Pass an initialized `ProcessedDataset` that possesses an empty `trips` list.<br>3. Verify system intercepts error |
| **Test material used** | `ProcessedDataset` containing `trips=[]` |
| **Expected result (test oracle)** | Call is rejected and system explicitly throws a `ValueError` protecting downstream operations. |
| **Comments** | Represents negative boundary testing |
| **Created by** | Othman |
| **Test environment(s)** | Python 3.10+, `.venv` MacOS |

| Test Case ID | `profile_unit_03` |
| :--- | :--- |
| **Description of test** | Application intercepts telemetry dataframes missing critical analytical variables |
| **Related requirement document details** | Feature 3 Telematics Extraction |
| **Pre-requisites for test** | Valid `ProcessedDataset` structure containing corrupted dataframe entries. |
| **Test procedure** | 1. Construct dataset lacking the `RPM` column.<br>2. Pass dataset to Builder.<br>3. System parses dataframe columns vs required sets |
| **Test material used** | Partial Pandas DataFrame `['Speed', 'MAF']` |
| **Expected result (test oracle)** | Process fails safely and system raises `ValueError` regarding missing columns. |
| **Comments** | None |
| **Created by** | Othman |
| **Test environment(s)** | Python 3.10+, `.venv` MacOS |

### 2.2 Backend Unit Testing: Fuel Estimation Engine

| Test Case ID | `estim_unit_01` |
| :--- | :--- |
| **Description of test** | Application calculates exact fuel estimates from valid interval telemetry |
| **Related requirement document details** | L/100km Fuel Estimation Module |
| **Pre-requisites for test** | Instantiated `VehicleProfile` (providing AFR) and `ProcessedTrip`. |
| **Test procedure** | 1. Read sequentially timed MAF and Speed data limits.<br>2. Run `calculate_trip_fuel_consumption`.<br>3. Evaluate numerical output type. |
| **Test material used** | Datetime continuous mock trip dataframe simulating acceleration. |
| **Expected result (test oracle)** | Application completes complex vectorized aggregations and returns a positive `float` value denoting L/100km efficiency. |
| **Comments** | Validates pandas vectorized math correctness. |
| **Created by** | Othman |
| **Test environment(s)** | Python 3.10+, `.venv` MacOS |

| Test Case ID | `estim_unit_02` |
| :--- | :--- |
| **Description of test** | Application gracefully handles trip segments exhibiting zero total distance. |
| **Related requirement document details** | L/100km Fuel Estimation Mathematical Bounds |
| **Pre-requisites for test** | Vehicle profile data is valid. |
| **Test procedure** | 1. Input dataset spanning 10 seconds where `Speed == 0` for all rows (stationary idling).<br>2. Run estimator method. |
| **Test material used** | Idling telemetry mock dataframe |
| **Expected result (test oracle)** | Application identifies `0` distance and proactively returns `numpy.NaN` rather than executing a literal "Division by Zero" crash. |
| **Comments** | Tests absolute mathematical boundaries |
| **Created by** | Othman |
| **Test environment(s)** | Python 3.10+, `.venv` MacOS |

| Test Case ID | `estim_unit_03` |
| :--- | :--- |
| **Description of test** | System rejects calculations if core physics metrics are missing |
| **Related requirement document details** | L/100km Fuel Estimation Stability Requirement |
| **Pre-requisites for test** | Estimator is initiated. |
| **Test procedure** | 1. Send simulated trip missing the `MAF` (Mass Air Flow) column.<br>2. Trigger module execution.<br>3. Module evaluates strict column dependency. |
| **Test material used** | Structurally corrupt dataframe `['Speed', 'Timestamp']`. |
| **Expected result (test oracle)** | Module logs an error and actively returns `numpy.NaN` safely halting the efficiency output. |
| **Comments** | Equivalence class: Corrupt Inputs |
| **Created by** | Othman |
| **Test environment(s)** | Python 3.10+, `.venv` MacOS |

---

## 3. Test Results Summary

| Test Case ID | Test Component | Status | Fault Severity (if failed) | Iteration |
| :--- | :--- | :--- | :--- | :--- |
| `profile_unit_01` | Profile Builder: Dynamic Payload | **PASS** | N/A | Cycle 1 |
| `profile_unit_02` | Profile Builder: Empty Rejection | **PASS** | N/A | Cycle 1 |
| `profile_unit_03` | Profile Builder: Column Validation | **PASS** | N/A | Cycle 1 |
| `estim_unit_01` | Estimator: Valid Aggregation | **PASS** | N/A | Cycle 1 |
| `estim_unit_02` | Estimator: 0-Div Prevention | **PASS** | N/A | Cycle 1 |
| `estim_unit_03` | Estimator: Validation Integrity | **PASS** | N/A | Cycle 1 |

---

## 4. Testing Context 

**Test Failure Severity Scale:**
To prioritize debugging efficiently, test failures are ranked upon discovery via the following matrix:
*   **High Severity (1):** Critical functional blockages (System completely crashes, produces corrupt/dangerous numeric data bypassing standard safety guards).
*   **Medium Severity (2):** Graceful degradation failure (System survives but does not output required deliverables; e.g., missing API fallback logic).
*   **Low Severity (3):** Inconvenient UI representations or minor non-fatal architectural warnings.

**Testing Environment and Tools:**
*   **OS/Hardware:** Executed locally via MacOS.
*   **Python Target:** Target compiled securely via an activated python virtual environment (`.venv`) ensuring dependency encapsulation.
*   **Test Framework Tools:** The Python standard `unittest` library was chosen over third-party alternatives to guarantee zero-dependency execution across different developer environments. `unittest.mock` operations are strictly utilized to avoid causing artificial rate-limiting against the external standard Cars API integrations during validation.