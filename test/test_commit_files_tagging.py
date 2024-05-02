from pandas import DataFrame
import pytest

from pandas.testing import assert_frame_equal

from src.commit_files_tagging import CommitFilesTagger


@pytest.mark.parametrize(
    "repo_struct,df,expected_df",
    [
        [
            {
                'src':{
                    'path':'./src',
                    'component':{
                        'nms':['view', 'control', 'model'],
                        'depth':1
                    },
                    'module_depth':1
                }
            },
            DataFrame([
                [None, 'src/test_view.php', None, None],
                [None, 'src/test_model.php', None, None],
                [None, 'src/test_control.php', None, None],
            ],
            columns=['commit_id', 'file_nm', 'nb_lines_inserted', 'nb_lines_deleted']
            ),
            DataFrame([
                [None, 'src/test_view.php', None, None, 'php', True, 'view', 'test'],
                [None, 'src/test_model.php', None, None,'php',  True, 'model', 'test'],
                [None, 'src/test_control.php', None, None, 'php', True, 'control', 'test'],
            ], columns=['commit_id', 'file_nm', 'nb_lines_inserted', 'nb_lines_deleted', 'ext', 'is_src', 'component_nm', 'module_nm'])
        ],
        [
            {
                'src':{
                    'path':'./src',
                    'component':None,
                    'module_depth':1
                }
            },
            DataFrame([
                [None, 'src/contact.php', None, None],
                [None, 'src/crm.php', None, None],
                [None, 'src/organization.php', None, None],
            ],
            columns=['commit_id', 'file_nm', 'nb_lines_inserted', 'nb_lines_deleted']
            ),
            DataFrame([
                [None, 'src/contact.php', None, None, 'php', True, 'contact'],
                [None, 'src/crm.php', None, None,'php',  True, 'crm'],
                [None, 'src/organization.php', None, None, 'php', True, 'organization'],
            ], columns=['commit_id', 'file_nm', 'nb_lines_inserted', 'nb_lines_deleted', 'ext', 'is_src', 'module_nm'])
        ],
        [
            {
                'src':{
                    'path':'./src',
                    'component':{
                        'nms':['view', 'control', 'model'],
                        'depth':1
                    },
                    'module_depth':1
                }
            },
            DataFrame([
                [None, 'src/test_view/abc.php', None, None],
                [None, 'src/test_model/def.php', None, None],
                [None, 'src/test_control/jql.php', None, None],
            ],
            columns=['commit_id', 'file_nm', 'nb_lines_inserted', 'nb_lines_deleted']
            ),
            DataFrame([
                [None, 'src/test_view/abc.php', None, None,'php', True, 'view', 'test'],
                [None, 'src/test_model/def.php', None, None,'php', True, 'model', 'test'],
                [None, 'src/test_control/jql.php', None, None,'php', True, 'control', 'test'],
            ], columns=['commit_id', 'file_nm', 'nb_lines_inserted', 'nb_lines_deleted', 'ext', 'is_src', 'component_nm', 'module_nm'])
        ],
        [
            {
                'src':{
                    'path':'./src',
                    'component':{
                        'nms':['view', 'control', 'model'],
                        'depth':2
                    },
                    'module_depth':1
                },
            },
            DataFrame([
                [None, 'src/test/view.php', None, None],
                [None, 'src/test/model.php', None, None],
                [None, 'src/test/control.php', None, None],
            ],
            columns=['commit_id', 'file_nm', 'nb_lines_inserted', 'nb_lines_deleted']
            ),
            DataFrame([
                [None, 'src/test/view.php', None, None, 'php', True, 'view', 'test'],
                [None, 'src/test/model.php', None, None, 'php', True, 'model', 'test'],
                [None, 'src/test/control.php', None, None, 'php', True, 'control', 'test'],
            ],columns=['commit_id', 'file_nm', 'nb_lines_inserted', 'nb_lines_deleted', 'ext', 'is_src', 'component_nm', 'module_nm']
            )
        ],
    ]
)
def test_tag(repo_struct, df, expected_df):

    try:
        component_nms = repo_struct['src']['component']['nms']
        component_depth = repo_struct['src']['component']['depth']
    except TypeError:
        component_nms = None
        component_depth = None

    tagger = CommitFilesTagger(
        df,
        src_path=repo_struct['src']['path'],
        module_depth=repo_struct['src']['module_depth'],
        component_nms=component_nms,
        component_depth=component_depth
    )

    tagger._CommitFilesTagger__tag()

    assert_frame_equal(
        tagger.get_tagged_files(),
        expected_df
    )