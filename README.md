# Insurance Fraud Detection - ML Baseline

This project provides a practical machine-learning baseline for insurance fraud detection and a lightweight frontend.

## What it does
- Generates a synthetic claims dataset (if you don't have one yet).
- Trains a fraud classifier with preprocessing and class imbalance handling.
- Evaluates fraud-focused metrics and saves artifacts.
- Provides a Streamlit frontend for single and batch predictions.

## Project structure
- `src/generate_sample_data.py` - creates `data/insurance_claims.csv`
- `src/train.py` - trains and evaluates model, saves outputs in `models/` and `reports/`
- `app.py` - Streamlit frontend for interactive fraud scoring
- `requirements.txt` - Python dependencies

## Quick start
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

python src/generate_sample_data.py
python src/train.py
streamlit run app.py
```

## Deployment

### Option 1: Render (recommended)
This repo includes a `render.yaml` blueprint and `Procfile`.

1. Push this project to GitHub.
2. In Render, choose **New +** -> **Blueprint**.
3. Connect your GitHub repo and deploy.
4. Set `MONGO_URI` only if you want MongoDB (optional).  
   If not set, the app automatically uses local JSON files in `data/`.

### Option 2: Streamlit Community Cloud
1. Push this project to GitHub.
2. Go to Streamlit Community Cloud and create a new app.
3. Select:
   - Repository: your repo
   - Branch: your branch
   - Main file path: `app.py`
4. Add optional secrets only if you use MongoDB:
   - `MONGO_URI`
   - `MONGO_DB_NAME`

### Option 3: Azure App Service (Linux)
This repo now includes:
- `startup.sh` for Streamlit startup on Azure
- `.github/workflows/azure-webapp-streamlit.yml` for CI/CD to Azure Web App

#### A) One-time Azure setup (Portal)
1. Create an **Azure Web App (Linux, Python 3.11)**.
2. In **Configuration -> Application settings**, add:
   - `SCM_DO_BUILD_DURING_DEPLOYMENT=true`
   - `WEBSITES_PORT=8000`
3. In **Configuration -> General settings -> Startup Command**, set:
   - `bash startup.sh`
4. If using MongoDB, add:
   - `MONGO_URI`
   - `MONGO_DB_NAME`

#### B) GitHub Actions deployment
1. Download the Web App **publish profile** from Azure Portal.
2. In GitHub repo settings, add secret:
   - `AZURE_WEBAPP_PUBLISH_PROFILE`
3. Edit workflow file `.github/workflows/azure-webapp-streamlit.yml`:
   - set `AZURE_WEBAPP_NAME` to your Azure Web App name
4. Push to `main` branch to trigger deployment.

#### C) Quick deploy with Azure CLI (optional)
```bash
az webapp config appsettings set --resource-group <rg-name> --name <webapp-name> --settings SCM_DO_BUILD_DURING_DEPLOYMENT=true WEBSITES_PORT=8000
az webapp config set --resource-group <rg-name> --name <webapp-name> --startup-file "bash startup.sh"
```

### Required files already present
- `requirements.txt`
- `.streamlit/config.toml`
- `Procfile`
- `render.yaml`

## Frontend features
- Single claim prediction form
- Batch CSV scoring and download
- Dashboard cards for threshold and model metrics
- Training data preview

## Outputs
- `models/fraud_model.joblib`
- `reports/metrics.json`
- `reports/classification_report.txt`

## Notes
- This is a baseline template to customize with real claims data.
- Target column expected by training script: `is_fraud` (0/1).
- Batch CSV input columns expected by frontend:
  `insurance_type, age, vehicle_age, claim_amount, annual_premium, incidents, witness_count, policy_type, collision_type, police_report`
