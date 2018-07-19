def clean_feature(feature):
    """Summary

    Args:
        feature (TYPE): Description
    """
    feature = feature.strip().replace("'", "")
    feature = feature.replace('\n', ' ')
    return feature
