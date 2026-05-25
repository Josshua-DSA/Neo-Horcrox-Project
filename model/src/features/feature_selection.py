"""Feature-selection helpers."""


def select_features(frame, feature_names):
    return frame.loc[:, feature_names]
