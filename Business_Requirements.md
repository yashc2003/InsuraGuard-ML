
### 1. Business Problem & Objectives

**Problem Statement**  
Insurance fraud (e.g., staged accidents, exaggerated injuries, fake claims) costs the industry billions annually (e.g., ~$80–$300B in the US alone across P&C lines). Manual review is slow, inconsistent, and misses subtle patterns. Fraudulent claims represent ~5–10% of total claims but are rare events, leading to high imbalance in data.

**Business Objectives**  
- Reduce overall fraud losses by 10–30% through early, accurate flagging of suspicious claims.  
- Improve claims processing efficiency: Auto-approve low-risk claims faster; route high-risk claims to SIU/special investigators.  
- Minimize false positives: Limit unnecessary investigations (which increase costs and frustrate genuine claimants).  
- Achieve high recall on fraudulent cases (catch as many frauds as possible) while maintaining acceptable precision.  
- Provide explainable outputs (e.g., feature importance, probability scores) for auditor/compliance review.  
- Enable scalable, real-time or near-real-time scoring for new claims.

**Success Metrics (KPIs)**  
- Fraud detection rate (Recall): ≥70–85% of known frauds flagged.  
- Precision: ≥20–40% (high due to rarity; aim to flag meaningful suspects without overwhelming SIU).  
- F1-Score or PR-AUC: Primary model selection metric.  
- Reduction in fraud leakage (estimated $ saved).  
- Investigation workload: Reduce manual reviews by 20–50% on low-risk claims.  
- Model false positive rate: <10–15% of total claims flagged for review.  
- System uptime & latency: <5 seconds per claim score (for API).

### 2. Functional Requirements

**Core Functionality**  
- Input: Accept structured claim data (JSON/CSV) including policy details, claimant info, incident description, claim amount, supporting docs metadata, history.  
- Processing: ML model scores each claim (0–1 probability of fraud).  
- Output: Fraud probability score + binary prediction (Fraud/Genuine) based on tunable threshold + top contributing features (for explainability).  
- Flagging logic: Claims above threshold routed to SIU queue; low-risk auto-processed.  
- Integration: Simple Flask API endpoint (/predict) for claims system to call.  
- Logging & Monitoring: Log predictions, actual outcomes (for retraining), drift detection alerts.

**Key User Stories / Use Cases**  
- As a claims adjuster, I want auto-flagging of high-risk claims so I can prioritize investigations.  
- As an SIU investigator, I want probability scores + feature explanations to focus on likely fraud.  
- As a business owner, I want model performance dashboards (confusion matrix, ROI estimates) to justify investment.  
- As a compliance officer, I want auditable decisions (no black-box) and bias checks.

### 3. Non-Functional Requirements

- **Performance** — Handle 1,000–10,000 claims/day initially; low latency scoring.  
- **Scalability** — Model retrainable on new data quarterly/annually.  
- **Security & Compliance** — Data anonymized/PII handled per GDPR/insurance regs; model bias mitigation; audit trails.  
- **Reliability** — Model fallback (e.g., rule-based if ML fails); version control (MLflow or similar).  
- **Usability** — Simple API; optional dashboard for monitoring.  
- **Maintainability** — Code modular; documentation; easy to update thresholds/models.

### 4. Scope & Out-of-Scope (for 30m Story/Prototype)

**In Scope**  
- Binary classification (Fraud vs Genuine).  
- Use of supervised ML (Random Forest, XGBoost as priorities).  
- Imbalance handling (SMOTE/class weights).  
- Basic evaluation (F1, PR-AUC, confusion matrix).  
- Flask API demo for single claim prediction.  
- Feature importance visualization.

**Out of Scope (Future Phases)**  
- Real-time streaming (Kafka).  
- Unsupervised/anomaly detection hybrid.  
- Network analysis (fraud rings).  
- Integration with external data (credit bureaus, social media).  
- Full production deployment (Docker/K8s, monitoring).  
- Advanced explainability (SHAP/LIME full suite).

### 5. Assumptions & Constraints

- Labeled historical claims data available (public Kaggle dataset for prototype).  
- Fraud is rare → imbalance handling critical.  
- Threshold tunable based on cost of FP vs FN (e.g., investigation cost ~$500–$2,000 vs fraud loss $5,000+).  
- No access to sensitive real PII in prototype.  
- Focus on auto insurance claims for simplicity.

### 6. Risks & Dependencies

**Risks**  
- High imbalance → poor model performance if not handled.  
- Over-flagging → increased operational costs.  
- Data quality issues (missing values, labeling errors).  
- Model drift as fraud patterns evolve.

**Dependencies**  
- Access to prerequisites resources (linked articles/videos).  
- Python environment with scikit-learn, xgboost, imbalanced-learn, flask.  
- Sample dataset (e.g., Kaggle insurance fraud datasets).

**Approval**  
[Space for sign-off from stakeholders]

This BRD sets clear expectations for the ML prototype while aligning with business value (cost savings + efficiency). It emphasizes fraud as a **cost-saving + risk-reduction** initiative rather than just tech.

If you'd like expansions (e.g., detailed use case diagrams, cost-benefit estimates, or a prioritized backlog), or adjustments for a specific insurance type (auto/health), let me know! Next step could be a high-level solution design or starter notebook outline.
