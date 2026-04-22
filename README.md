## Overview
Intelligent Customer Reconciliation and Claims Resolution for Organised Trade & D2C Channels.

## Features
- Automated data ingestion from SAP and customer statements
- Rule-based matching engine with 3 matching strategies
- Mismatch classification and auto-resolution
- REST API with Swagger documentation
- Web dashboard for real-time visibility

## Tech Stack
- Python 3.x
- FastAPI (REST API)
- SQLAlchemy (ORM)
- SQLite (Development) / PostgreSQL (Production)
- HTML/CSS/JS Dashboard

## Setup Instructions

### 1. Install dependencies
\`\`\`bash
pip install -r requirements.txt
\`\`\`

### 2. Initialize database
\`\`\`bash
python setup_db.py
\`\`\`

### 3. Ingest sample data
\`\`\`bash
python ingest_data.py
\`\`\`

### 4. Run reconciliation
\`\`\`bash
python run_reconciliation.py
\`\`\`

### 5. Start API server
\`\`\`bash
python run_api.py
\`\`\`

### 6. Open dashboard
Visit: http://localhost:8000/

## API Endpoints
- GET /api/dashboard/summary - KPI dashboard data
- GET /api/dashboard/mismatches - List all mismatches
- GET /api/dashboard/claims - List all claims
- POST /api/resolve/{invoice_number} - Resolve a mismatch
- PUT /api/claims/{claim_number} - Update claim status

## Sample Data Included
- 4 invoices from SAP
- 5 customer statement transactions
- 2 mismatches (₹500 and ₹2000 differences)
- 2 auto-generated claims

## Business Impact
- Reduction in reconciliation cycle from months to days
- Automated mismatch detection and classification
- Real-time visibility into blocked working capital
- Improved customer trust and transparency

## Author
Aman Paliwal
