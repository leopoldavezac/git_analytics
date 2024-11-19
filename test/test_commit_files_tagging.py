from pandas import DataFrame
import pytest

from pandas.testing import assert_frame_equal
from src.data_preparation import tag_commit_files

@pytest.mark.parametrize(
    "config_manager,df,expected_df",
    [
        [
            {
                'src_path': './src',
                'module_depth': 1,
                'component_nms': ['view', 'control', 'model'],
                'component_depth': 1
            },
            DataFrame([
                [None, 'src/test_view.php', None, None],
                [None, 'src/test_model.php', None, None],
                [None, 'src/test_control.php', None, None],
            ],
            columns=['commit_id', 'file_path', 'nb_lines_inserted', 'nb_lines_deleted']
            ),
            DataFrame([
                [None, 'src/test_view.php', None, None, 'php', True, 'view', 'test'],
                [None, 'src/test_model.php', None, None, 'php', True, 'model', 'test'],
                [None, 'src/test_control.php', None, None, 'php', True, 'control', 'test'],
            ], columns=['commit_id', 'file_path', 'nb_lines_inserted', 'nb_lines_deleted', 'ext', 'is_src', 'component_nm', 'module_nm'])
        ],
        [
            {
                'src_path': './src',
                'module_depth': 1,
                'component_nms': None,
                'component_depth': None
            },
            DataFrame([
                [None, 'src/contact.php', None, None],
                [None, 'src/crm.php', None, None],
                [None, 'src/organization.php', None, None],
            ],
            columns=['commit_id', 'file_path', 'nb_lines_inserted', 'nb_lines_deleted']
            ),
            DataFrame([
                [None, 'src/contact.php', None, None, 'php', True, 'contact'],
                [None, 'src/crm.php', None, None, 'php', True, 'crm'],
                [None, 'src/organization.php', None, None, 'php', True, 'organization'],
            ], columns=['commit_id', 'file_path', 'nb_lines_inserted', 'nb_lines_deleted', 'ext', 'is_src', 'module_nm'])
        ],
        [
            {
                'src_path': './src',
                'module_depth': 1,
                'component_nms': ['view', 'control', 'model'],
                'component_depth': 1
            },
            DataFrame([
                [None, 'src/test_view/abc.php', None, None],
                [None, 'src/test_model/def.php', None, None],
                [None, 'src/test_control/jql.php', None, None],
            ],
            columns=['commit_id', 'file_path', 'nb_lines_inserted', 'nb_lines_deleted']
            ),
            DataFrame([
                [None, 'src/test_view/abc.php', None, None, 'php', True, 'view', 'test'],
                [None, 'src/test_model/def.php', None, None, 'php', True, 'model', 'test'],
                [None, 'src/test_control/jql.php', None, None, 'php', True, 'control', 'test'],
            ], columns=['commit_id', 'file_path', 'nb_lines_inserted', 'nb_lines_deleted', 'ext', 'is_src', 'component_nm', 'module_nm'])
        ],
        [
            {
                'src_path': './src',
                'module_depth': 1,
                'component_nms': ['view', 'control', 'model'],
                'component_depth': 2
            },
            DataFrame([
                [None, 'src/test/view.php', None, None],
                [None, 'src/test/model.php', None, None],
                [None, 'src/test/control.php', None, None],
            ],
            columns=['commit_id', 'file_path', 'nb_lines_inserted', 'nb_lines_deleted']
            ),
            DataFrame([
                [None, 'src/test/view.php', None, None, 'php', True, 'view', 'test'],
                [None, 'src/test/model.php', None, None, 'php', True, 'model', 'test'],
                [None, 'src/test/control.php', None, None, 'php', True, 'control', 'test'],
            ], columns=['commit_id', 'file_path', 'nb_lines_inserted', 'nb_lines_deleted', 'ext', 'is_src', 'component_nm', 'module_nm'])
        ],
    ]
)
def test_tag(config_manager, df, expected_df):
    df = tag_commit_files(df, config_manager)

    assert_frame_equal(df, expected_df)
