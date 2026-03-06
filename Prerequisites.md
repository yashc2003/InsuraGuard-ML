# InsuraGuard-ML
# Prerequisites for Insurance Fraud Detection Using Machine Learning

**Project Story Duration:** 30 minutes  
**Assigned to:** Sahil Subudhi  
**Goal:** Build a basic understanding of key ML concepts, algorithms, evaluation techniques, and deployment basics needed to implement an insurance claims fraud detection model (typically a supervised binary classification task on imbalanced data).

## 1. Core Machine Learning Concepts

- **Supervised Learning**  
  → When we have labeled data (fraud = 1 / genuine = 0) and want to learn a mapping from features to labels.  
  Key resource: [Supervised Machine Learning - Javatpoint](https://www.javatpoint.com/supervised-machine-learning)  
  Must-know: Classification vs Regression, training/validation/test split, overfitting/underfitting.

- **Unsupervised Learning** (optional but useful for anomaly detection approaches)  
  → Finding patterns without labels (e.g., clustering suspicious claims or detecting outliers).  
  Key resource: [Unsupervised Machine Learning - Javatpoint](https://www.javatpoint.com/unsupervised-machine-learning)  
  Must-know: Clustering (K-Means), Dimensionality Reduction (PCA), Anomaly Detection basics.

## 2. Key Algorithms to Understand (Focus on these for the project)

- **Decision Tree**  
  → Simple, interpretable tree-based model. Good for understanding rules (e.g., "no police report + high claim amount → suspicious").  
  Resource: [Decision Tree Classification - Javatpoint](https://www.javatpoint.com/machine-learning-decision-tree-classification-algorithm)

- **Random Forest**  
  → Ensemble of decision trees → reduces overfitting, handles imbalance better, gives feature importance.  
  Resource: [Random Forest Algorithm - Javatpoint](https://www.javatpoint.com/machine-learning-random-forest-algorithm)  
  → Usually a strong baseline for tabular fraud data.

- **K-Nearest Neighbors (KNN)**  
  → Distance-based classifier. Simple but needs good scaling and suffers in high dimensions.  
  Resource: [K-Nearest Neighbor Algorithm - Javatpoint](https://www.javatpoint.com/k-nearest-neighbor-algorithm-for-machine-learning)

- **XGBoost**  
  → Gradient boosting → often the best performer on structured/tabular data like insurance claims. Handles missing values, imbalance (via scale_pos_weight), and gives excellent feature importance.  
  Resource: [End-to-End Guide to XGBoost - Analytics Vidhya](https://www.analyticsvidhya.com/blog/2018/09/an-end-to-end-guide-to-understand-the-math-behind-xgboost/)

## 3. Evaluation Metrics (Very Important – Fraud data is imbalanced!)

Don't use accuracy alone!  
Key resource: [11 Important Model Evaluation Error Metrics - Analytics Vidhya](https://www.analyticsvidhya.com/blog/2019/08/11-important-model-evaluation-error-metrics/)

Must-know metrics:
- Confusion Matrix (TP, TN, FP, FN)
- Precision (low false alarms → don't annoy genuine claimants)
- Recall / Sensitivity (catch as many frauds as possible → save money)
- F1-Score (harmonic mean of precision & recall)
- ROC-AUC
- Precision-Recall AUC (PR-AUC – usually better for imbalanced classes)
- Business metric example: Cost of false negatives (missed fraud) vs cost of false positives (manual review)

## 4. Deployment Basics

- **Flask** – Lightweight web framework to serve the model as an API (e.g., POST claim data → get fraud probability).  
  Key resource: [Flask Basics Tutorial (YouTube)](https://www.youtube.com/watch?v=lj4I_CvBnt0)  
  → Learn: Create app, routes, request.json, return jsonify, load model with joblib/pickle.

## Recommended Python Libraries (Install via pip / conda)

```bash
pip install pandas numpy scikit-learn imbalanced-learn xgboost matplotlib seaborn joblib flask
# Optional extras: lightgbm, catboost, plotly (for better viz)
