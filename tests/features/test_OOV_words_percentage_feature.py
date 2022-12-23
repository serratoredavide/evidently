import pandas as pd

from evidently import ColumnMapping
from evidently.features.OOV_words_percentage_feature import OOVWordsPercentage
from evidently.utils.data_preprocessing import create_data_definition


def test_oov_words_percentage():
    feature_generator = OOVWordsPercentage("column_1", ignore_words=("foobar",))
    data = pd.DataFrame(dict(column_1=["Who ate apples? Go iaehb!", "Who ate apples? Go foobar! ", "the"]))
    result = feature_generator.generate_feature(
        data=data,
        data_definition=create_data_definition(None, data, ColumnMapping()),
    )
    assert result.equals(pd.DataFrame(dict(column_1=[20.0, 0, 0])))
