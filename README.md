# Onion Quality Assessment & Grading System

A production-ready end-to-end computer vision and deterministic rules engine application for automated onion quality grading (Grade A, URS, Non-Compliant) compliant with NAFED guidelines.

---

## Core System Architecture & Principles

1. **Roboflow Model as Vision Evidence Only**:
   - Model ID: `veg1-hcqsf-2/4` (YOLOv8x Object Detection)
   - Detected Classes: `onion`, `Black smut`, `double_split`, `Spoiled`, `sprouted`, `Staining`
   - Reported Metrics: mAP@50 43.4%, Precision 57.3%, Recall 51.5%.
   - **Crucial Rule**: The vision model ONLY detects bounding box visual evidence. It NEVER predicts "Grade A", "URS", or "Reject".

2. **Deterministic Rules Engine**:
   - All final grading decisions are made by a separate non-ML rules engine adhering strictly to `grading_standards.json`.

3. **Onion Instance Spatial Association**:
   - Every detected defect (`sprouted`, `spoiled`, `double_split`, `black_smut`, `staining`) is associated to the nearest/overlapping onion using Intersection-over-Union (IoU) and spatial containment. Defects are **NEVER counted globally**.

4. **OpenCV Calibration & Measurement**:
   - Reference coin (e.g. 23mm diameter) or ArUco marker detection converts bounding-box pixel geometry into physical millimeters.
   - Tagged explicitly as `measurement_method: bounding_box_estimate`.
   - If no reference coin is detected, `diameter_mm` is set to `null` with warning message.

---

## Pipeline Execution Order

```
Image 
  → RoboflowService 
  → OnionAssociationService (match defects to onions via IoU)
  → CalibrationService (reference coin/marker detection)
  → SizeMeasurementService (pixel-to-mm conversion)
  → GradingEngine (deterministic rules against grading_standards.json)
  → BatchAnalysisService (multi-image aggregation)
  → ReportService (PDF report generation)
```

---

## Directory Structure

```
Model/
├── .env.example                     # Environment template
├── README.md                        # Setup and documentation
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI server endpoints
│   │   ├── config.py                # Environment configuration
│   │   ├── models.py                # Pydantic schemas
│   │   ├── data/
│   │   │   └── grading_standards.json # Deterministic rules config
│   │   └── services/
│   │       ├── roboflow_service.py   # Roboflow API integration & fallback
│   │       ├── association_service.py# IoU defect-to-onion matching
│   │       ├── calibration_service.py# OpenCV reference coin detector
│   │       ├── measurement_service.py# Size measurement (px to mm)
│   │       ├── grading_engine.py     # Deterministic Grade A/URS engine
│   │       ├── batch_service.py     # Batch analysis aggregator
│   │       └── report_service.py    # ReportLab PDF generator
│   ├── generate_samples_and_test.py # Automated test suite (Phases 1-7)
│   └── requirements.txt             # Python dependencies
└── frontend/                        # Next.js 14+ Tailwind CSS TypeScript App
    ├── src/
    │   ├── app/page.tsx             # Main operational UI (7 pages)
    │   ├── components/
    │   │   ├── Header.tsx           # Navigation & status bar
    │   │   ├── BoundingBoxCanvas.tsx# Interactive canvas visualizer
    │   │   ├── IndividualOnionCard.tsx# Explainable breakdown card
    │   │   └── TechnicalDetailsAccordion.tsx # ML jargon accordion
    │   └── types/onion.ts           # TypeScript interfaces
```

---

## Setup & Running Instructions

### 1. Backend Setup (FastAPI + Python)

1. Open shell in `backend/`:
   ```bash
   cd backend
   ```

2. Create & activate Python virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure `.env`:
   ```bash
   cp .env.example .env
   ```
   Add your `ROBOFLOW_API_KEY=your_actual_key` if available. If no key is provided, system runs seamlessly with built-in computer vision fallback detection!

5. Run Automated Pipeline Test Suite (Phases 1-7):
   ```bash
   python generate_samples_and_test.py
   ```

6. Start FastAPI Backend Server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

---

### 2. Frontend Setup (Next.js + TypeScript + Tailwind CSS)

1. Open shell in `frontend/`:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start Next.js Development Server:
   ```bash
   npm run dev
   ```

4. Open browser at `http://localhost:3000`.

---

## Application Pages & Workflows

1. **Dashboard**: High-level overview of total onions inspected, Grade A %, URS %, Non-Compliant %, core rules compliance overview.
2. **Analyze Image**: Single image upload, interactive bounding box visualizer canvas, 3 mandatory distinct sections (**AI DETECTION**, **SPATIAL MEASUREMENT**, **DETERMINISTIC GRADING**), technical ML details accordion, individual onion explainable breakdown cards.
3. **Batch Analysis**: Process multi-image lots, compute mean/median/min/max size distribution statistics, export PDF report.
4. **Onion Inspector**: Filterable audit trail for every onion instance.
5. **Quality Report**: Formal PDF quality report preview & download with mandatory technical disclosures and warnings.
6. **Grading Standards**: Visual and raw JSON editor for `grading_standards.json`.
7. **Settings**: API Key management, confidence threshold sliders, calibration reference defaults.
