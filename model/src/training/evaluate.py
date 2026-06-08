"""Model evaluation helpers."""

from sklearn.metrics import classification_report


def classification_metrics(y_true, y_pred):
    return classification_report(y_true, y_pred, output_dict=True)
