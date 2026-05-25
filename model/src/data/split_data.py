"""Dataset split helpers."""

from sklearn.model_selection import train_test_split


def split_train_test(frame, target_column: str, test_size: float = 0.2, random_state: int = 42):
    features = frame.drop(columns=[target_column])
    target = frame[target_column]
    return train_test_split(features, target, test_size=test_size, random_state=random_state)
