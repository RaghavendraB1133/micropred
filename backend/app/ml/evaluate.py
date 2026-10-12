import numpy as np
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, confusion_matrix, brier_score_loss
)
from sklearn.linear_model import LogisticRegression
from typing import Dict, Any
from app.utils.logger import logger

def evaluate_model_predictions(
    y_true: np.ndarray,
    y_pred_proba: np.ndarray,
    threshold: float = 0.5
) -> Dict[str, Any]:
    """
    Computes rigorous classification metrics on an untouched chronological test set.
    """
    y_pred_binary = (y_pred_proba >= threshold).astype(int)
    
    # Avoid zero-division errors with zero_division parameter
    acc = float(accuracy_score(y_true, y_pred_binary))
    prec = float(precision_score(y_true, y_pred_binary, zero_division=0))
    rec = float(recall_score(y_true, y_pred_binary, zero_division=0))
    f1 = float(f1_score(y_true, y_pred_binary, zero_division=0))
    
    try:
        auc = float(roc_auc_score(y_true, y_pred_proba))
    except Exception:
        auc = 0.5

    brier = float(brier_score_loss(y_true, y_pred_proba))
    cm = confusion_matrix(y_true, y_pred_binary).tolist()

    return {
        'threshold': threshold,
        'accuracy': round(acc, 4),
        'precision': round(prec, 4),
        'recall': round(rec, 4),
        'f1_score': round(f1, 4),
        'roc_auc': round(auc, 4),
        'brier_score': round(brier, 4),
        'confusion_matrix': cm,
        'test_samples': int(len(y_true)),
        'positive_samples': int(np.sum(y_true))
    }

def evaluate_baseline_comparison(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray
) -> Dict[str, Any]:
    """
    Trains and evaluates a simple Logistic Regression baseline using flattened sequence features.
    """
    # Flatten (N, T, D) -> (N, T*D)
    N_train, T, D = X_train.shape
    X_train_flat = X_train.reshape(N_train, T * D)
    N_test = X_test.shape[0]
    X_test_flat = X_test.reshape(N_test, T * D)

    clf = LogisticRegression(max_iter=1000, random_state=42)
    clf.fit(X_train_flat, y_train)
    y_pred_proba = clf.predict_proba(X_test_flat)[:, 1]

    metrics = evaluate_model_predictions(y_test, y_pred_proba)
    logger.info(f"Baseline Logistic Regression: Accuracy={metrics['accuracy']}, F1={metrics['f1_score']}, AUC={metrics['roc_auc']}")
    return metrics
