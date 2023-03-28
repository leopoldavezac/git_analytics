import pandas as pd
import numpy as np
import pytest

from pandas.testing import assert_frame_equal

from git_analytics.fig_generation import Transformer


DF_COMMITS = pd.DataFrame(
    [
        ['29ee2a8bc32e1a6b0d08d89368451628e71b8717', '2022-04-27 14:58:11+01:00', 'dev_2', 'test: adding some tests'],
        ['c9b34e0289f67637e0905b094ce858848f07b2e2', '2022-02-19 17:40:00+01:00', 'dev_2', 'fix: cleaning up the mess'],
        ['9df52fbfdc5795bc021e2c27965fe46d9370e233', '2022-02-19 17:26:20+01:00', 'dev_1', 'fix: no more bugs'],
        ['19d30f1897a38a93cd0c07da15965a7492cebd2e', '2022-01-19 09:33:33+01:00', 'dev_3', 'fix: a fix with some more bugs'],
        ['0b2b9882f2649d567e0611bd8050ac7a91947c6d', '2022-01-18 10:49:31+01:00', 'dev_1', 'feat: a feat with a lot of bugs'],
    ], columns=['id', 'creation_dt', 'author_nm', 'msg']
)

DF_COMMITS_FILES = pd.DataFrame(
    [
        ['29ee2a8bc32e1a6b0d08d89368451628e71b8717', 'src/shitty_code_view.php', 10, 2, 'php', True, 'view', 'shitty_code', 'dev_1', '2022-04-27 14:58:11+01:00'],
        ['29ee2a8bc32e1a6b0d08d89368451628e71b8717', 'src/shitty_code_model.php', 20, 1, 'php', True, 'model', 'shitty_code', 'dev_1', '2022-04-27 14:58:11+01:00'],
        ['29ee2a8bc32e1a6b0d08d89368451628e71b8717', 'src/shitty_code_controller.php', 5, 1, 'php', True, 'controller', 'shitty_code', 'dev_1', '2022-04-27 14:58:11+01:00'],
        ['c9b34e0289f67637e0905b094ce858848f07b2e2', 'src/shitty_code_view.php', 10, 2, 'php', True, 'view', 'shitty_code', 'dev_2', '2022-02-19 17:40:00+01:00'],
        ['c9b34e0289f67637e0905b094ce858848f07b2e2', 'src/shitty_code_model.php', 30, 2, 'php', True, 'model', 'shitty_code', 'dev_3', '2022-02-19 17:40:00+01:00'],
        ['c9b34e0289f67637e0905b094ce858848f07b2e2', 'src/shittier_code_view.php', 40, 0, 'php', True, 'view', 'shittier_code', 'dev_2', '2022-02-19 17:40:00+01:00'],
        ['9df52fbfdc5795bc021e2c27965fe46d9370e233', 'src/shittier_code_model.php', 5, 2, 'php', True, 'model', 'shittier_code', 'dev_3', '2022-02-19 17:40:00+01:00'],
        ['0b2b9882f2649d567e0611bd8050ac7a91947c6d', 'src/shittier_code_controller.php', 10, 2, 'php', True, 'controller', 'shittier_code', 'dev_3', '2022-02-19 17:40:00+01:00'],
        
    ], columns=['commit_id', 'file_nm', 'n_lines_inserted', 'n_lines_deleted', 'ext', 'is_src', 'component_nm', 'module_nm', 'author_nm', 'creation_dt']
)

@pytest.mark.parametrize(
    'concept,entity,mesure,normalize_axis,aggfunc,freq,unstack_level,df,expected_df',
    [
        [
            'stability', 'author_nm', 'id', 1, 'count', 'M', 0, DF_COMMITS,
            pd.DataFrame(
                [
                    [0.5, 0.5, np.nan, np.nan],
                    [np.nan, 0.5, np.nan, 1],
                    [0.5, np.nan, np.nan, np.nan],
                ],
                columns=pd.DatetimeIndex(
                    pd.to_datetime(['2022-01-31 00:00:00+01:00', '2022-02-28 00:00:00+01:00', '2022-03-31 00:00:00+01:00', '2022-04-30 00:00:00+01:00']),
                    name='creation_dt',
                    ),
                index=pd.Index(['dev_1', 'dev_2', 'dev_3'], name='author_nm')
            ),
        ],
        [
            'specialization', ['author_nm', 'module_nm'], 'n_lines_inserted', 1, 'sum', 'M', 0, DF_COMMITS_FILES,
            pd.DataFrame(
                [
                    [np.nan, 0.47],
                    [0.73, 0.13],
                    [0.27, 0.4],
                ],
                index=pd.Index(['dev_1', 'dev_2', 'dev_3'], name='author_nm'),
                columns=pd.Index(['shittier_code', 'shitty_code'], name='module_nm')
            ),
        ],
        [
            'evolution', None, 'id', None, 'count', 'M', None, DF_COMMITS,
            pd.DataFrame(
                [
                    ['2022-01-31 00:00:00+01:00', 2],
                    ['2022-02-28 00:00:00+01:00', 2],
                    ['2022-03-31 00:00:00+01:00', 0],
                    ['2022-04-30 00:00:00+01:00', 1],
                ],
                columns=pd.Index(['creation_dt', 'id'])
            ).assign(creation_dt = lambda dfx: pd.to_datetime(dfx.creation_dt)),
        ],
        [
            'size', 'module_nm', 'commit_id', None, 'nunique', None, None, DF_COMMITS_FILES,
            pd.DataFrame(
                [
                    ['shittier_code', 3],
                    ['shitty_code', 2]
                ],
                columns=pd.Index(['module_nm', 'commit_id'])
            ),
        ],
    ]
)
def test_get_transformed(concept, entity, mesure, normalize_axis, aggfunc, freq, unstack_level, df, expected_df):
    
    transformer = Transformer(concept, mesure, entity, normalize_axis, aggfunc, freq, unstack_level)
    obtained_df = transformer.get_transformed((
        df
        .assign(creation_dt = lambda dfx: pd.to_datetime(dfx.creation_dt))
        .set_index('creation_dt')
        )
    )

    assert_frame_equal(expected_df, obtained_df)

