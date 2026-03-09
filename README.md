[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/B06_mcpV)

## Group Roles


* *Tam: Data Engineer / Pipeline Manager (ETL)* - Features 1, 2, 9. Ingestion, validation, trip segmentation, data quality.
* *Othman: Data Scientist / Analytics Engineer (Modeling)* - Features 3, 4. Vehicle calibration, fuel estimation models.
* *Hamzah: Data Scientist / Backend (Behaviour)* - Features 5, 6. Inefficient behaviour detection, trip efficiency scoring.
* *Martin: AI/LLM Engineer (Granite Integration)* - Features 7, 10. AI coaching messages, fuel strategy advice, prompt engineering.
* *Francis: Frontend Developer (Dashboard)* - Feature 8. Dashboard, visual trends, UI/UX.

### Repo Structure

```text
ecogranite-coach/
│
├── data_pipeline/          # Features 1, 2, 3, 9
│   ├── ingestion/          # CSV validation, missing value handling
│   ├── segmentation/       # Trip splitting (10-min gaps), vehicle identification
│   └── profiles/           # Vehicle threshold calibrations
│
├── analytics_engine/       # Features 4, 5, 6
│   ├── fuel_estimation/    # Fuel usage models, L/100km calculations
│   ├── event_detection/    # High-RPM, harsh throttle, hard braking logic
│   └── scoring/            # 0-100 efficiency score logic
│
├── ai_coaching/            # Features 7, 10
│   ├── granite_client/     # API wrappers for IBM Granite
│   └── prompts/            # Templates for trip feedback & strategy advice
│
├── backend/                # API connecting the pipeline/AI to the Frontend
│   ├── routes/             # REST/GraphQL endpoints for the dashboard
│   ├── database/           # SQLite/PostgreSQL for storing processed trips & metadata
│   └── core/               # App configuration, logging, and schemas
│
├── frontend/               # Feature 8
│   ├── components/         # Reusable UI widgets (charts, scorecards)
│   ├── pages/              # Trip Dashboard, Detailed Trip View
│   └── services/           # API fetching logic
│
├── tests/                  # Automated tests based on your Gherkin scenarios
│   ├── unit/               
│   └── integration/        
│
├── docs/                   # Markdown files, API docs, and Agile sprint logs
├── data_samples/           # Small, anonymized KIT datasets for local testing
├── .gitignore
└── README.md
```