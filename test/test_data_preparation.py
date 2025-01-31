import os

from numpy import nan
import pandas as pd

import pytest

from pandas.testing import assert_frame_equal

from src.config_management import ConfigManager

from src.data_preparation import handle_file_renaming

import src.data_preparation
import src.utilities
import src.cmd_chaining
import src.git_log_parsing



def test_integration_prep_data(mocker):

    config_manager = ConfigManager()
    config_manager.codebase_nm = 'random_reward_bot'
    config_manager.path_to_repo = "./test/asset/repo/RandomRewardBot"
    config_manager.src_path = './random_reward_bot'
    config_manager.module_depth = 1
    
    mocker.patch.object(
        src.utilities,
        'DATA_PATH',
        './test/temp/data'
        )
    mocker.patch.object(
        src.cmd_chaining,
        'DATA_PATH',
        './test/temp/data'
        )
    mocker.patch.object(
        src.git_log_parsing,
        'DATA_PATH',
        './test/temp/data'
        )

    EXPECTED_COMMITS = (
            pd.DataFrame(
                [
                    ['8e0a7079f73a4341398458351477c9edbbae2064', '2021-09-30 15:12:01 +0200', 'leopoldavezac','chore(rewards) - update yaml file'],
                    ['ea39952af8fae82d98537a42e87be6f933468d4b', '2021-09-30 15:04:49 +0200', 'leopoldavezac','chore(requirements) - none'],
                    ['58dcfab39bb0d389e04a09fefb347395939af360', '2021-09-30 15:03:45 +0200', 'leopoldavezac','refactor(app) - relative import'],
                    ['72a8f13827b42b2010098967533642b45e19bcd0', '2021-09-30 15:02:09 +0200', 'leopoldavezac','fix(rewards) - money as str'],
                    ['301c4e985455b96f1d6142642161716ba3130c73', '2021-09-29 15:58:58 +0200', 'leopoldavezac','chore(packaging) - install module for easy import'],
                    ['7f1a63ff379c0bd6a5cabc56dc46ab223e90d45e', '2021-09-29 15:58:07 +0200', 'leopoldavezac','chore(gitignore) - ignore cache and egg info'],
                    ['a2140d0462144ab0e58ee801a50b555fafde7a1f', '2021-09-29 15:56:31 +0200', 'leopoldavezac','feat(reward) - return (or not) reward to user'],
                    ['da89518e033844b5d1d7947fc9a407257f3c6184', '2021-09-29 15:35:08 +0200', 'leopoldavezac','refactoring(app) - renaming variables'],
                    ['4cc0ae168567f860bb58a1ac5d985e59d2ece5bd', '2021-09-29 14:23:08 +0200', 'leopoldavezac','feat(app) - return input msg as is'],
                    ['f44310f347a0144523c0393ab3fa217a907819d4', '2021-09-30 15:14:23 +0200', "Leopold d'Avezac",'Initial commit'],
                ],
                columns=['id', 'creation_dt', 'author_nm', 'msg']
        )
        .astype({
            'id':'string',
            'author_nm':'string',
            'msg':'string',
        })
        .assign(creation_dt = lambda dfx: pd.to_datetime(dfx.creation_dt, utc=True))
    )

    EXPECTED_COMMITS_FILES = (
        pd.DataFrame(
            [
                ['8e0a7079f73a4341398458351477c9edbbae2064', '2021-09-30 15:12:01 +0200', 'leopoldavezac','rewards.yaml', 2, 1, 'other', False, nan],
                ['ea39952af8fae82d98537a42e87be6f933468d4b', '2021-09-30 15:04:49 +0200', 'leopoldavezac','requirements.txt', 24, 0, 'other', False, nan],
                ['58dcfab39bb0d389e04a09fefb347395939af360', '2021-09-30 15:03:45 +0200', 'leopoldavezac','random_reward_bot/app.py', 1, 1, 'py', True, 'app'],
                ['58dcfab39bb0d389e04a09fefb347395939af360', '2021-09-30 15:03:45 +0200', 'leopoldavezac','setup.py', 0, 17, 'py', False, nan],
                ['72a8f13827b42b2010098967533642b45e19bcd0', '2021-09-30 15:02:09 +0200', 'leopoldavezac','rewards.yaml', 5, 5, 'other', False, nan],
                ['301c4e985455b96f1d6142642161716ba3130c73', '2021-09-29 15:58:58 +0200', 'leopoldavezac','setup.py', 17, 0, 'py', False, nan],
                ['7f1a63ff379c0bd6a5cabc56dc46ab223e90d45e', '2021-09-29 15:58:07 +0200', 'leopoldavezac','.gitignore', 4, 0, 'other', False, nan],
                ['a2140d0462144ab0e58ee801a50b555fafde7a1f', '2021-09-29 15:56:31 +0200', 'leopoldavezac','random_reward_bot/app.py', 6, 2, 'py', True, 'app'],
                ['a2140d0462144ab0e58ee801a50b555fafde7a1f', '2021-09-29 15:56:31 +0200', 'leopoldavezac','random_reward_bot/rewards.py', 29, 0, 'py', True, 'rewards'],
                ['a2140d0462144ab0e58ee801a50b555fafde7a1f', '2021-09-29 15:56:31 +0200', 'leopoldavezac','rewards.yaml', 12, 0, 'other', False, nan],
                ['da89518e033844b5d1d7947fc9a407257f3c6184', '2021-09-29 15:35:08 +0200', 'leopoldavezac','random_reward_bot/app.py', 3, 3, 'py', True, 'app'],
                ['4cc0ae168567f860bb58a1ac5d985e59d2ece5bd', '2021-09-29 14:23:08 +0200', 'leopoldavezac','random_reward_bot/app.py', 20, 0, 'py', True, 'app'],
                ['f44310f347a0144523c0393ab3fa217a907819d4', '2021-09-30 15:14:23 +0200', "Leopold d'Avezac",'LICENSE', 21, 0, 'other', False, nan],
                ['f44310f347a0144523c0393ab3fa217a907819d4', '2021-09-30 15:14:23 +0200', "Leopold d'Avezac",'README.md', 2, 0, 'other', False, nan],
            ],
            columns=['commit_id', 'creation_dt', 'author_nm', 'file_path', 'n_lines_inserted', 'n_lines_deleted', 'ext', 'is_src', 'module_nm']
        )
        .astype({
            'commit_id': 'string',
            'author_nm': 'string',
            'file_path': 'string',
            'n_lines_inserted': 'uint32',
            'n_lines_deleted': 'uint32',
            'ext': 'string',
            'is_src': 'bool',
            'module_nm': 'string',
        })
        .assign(creation_dt=lambda dfx: pd.to_datetime(dfx.creation_dt, utc=True))
        .loc[:, ['commit_id', 'file_path', 'n_lines_inserted', 'n_lines_deleted', 'ext', 'is_src', 'module_nm', 'author_nm', 'creation_dt']]
    )

    os.system('unzip test/asset/repo.zip') #test repo is stored as zip to avoid maintaning two git repo

    # mock config manager get func
    mocker.patch('src.data_preparation.instanciate_config_manager', return_value=config_manager)
    src.data_preparation.main()

    obtained_commits = pd.read_parquet('./test/temp/data/random_reward_bot_clean_commit.parquet')
    obtained_commits_files = pd.read_parquet('./test/temp/data/random_reward_bot_clean_commit_file.parquet')
  
    assert_frame_equal(EXPECTED_COMMITS, obtained_commits)
    assert_frame_equal(EXPECTED_COMMITS_FILES, obtained_commits_files)

    os.system('rm -R test/asset/repo')
    os.system('rm test/temp/data/*')




@pytest.mark.parametrize(
    'input_df,expected_df',
    [
        [
            pd.DataFrame(
                [
                    ['8e0a7079f73a4341398458351477c9edbbae2064', 'src/old_file_nm.cpp'],
                    ['ea39952af8fae82d98537a42e87be6f933468d4b', 'src/{old_file_nm.cpp => new_file_nm.cpp}'],
                    ['58dcfab39bb0d389e04a09fefb347395939af360', 'src/new_file_nm.cpp'],
                ],
                columns = ['commit_id', 'file_path']
            ),
            pd.DataFrame(
                [
                    ['8e0a7079f73a4341398458351477c9edbbae2064', 'src/new_file_nm.cpp'],
                    ['ea39952af8fae82d98537a42e87be6f933468d4b', 'src/new_file_nm.cpp'],
                    ['58dcfab39bb0d389e04a09fefb347395939af360', 'src/new_file_nm.cpp'],
                ],
                columns = ['commit_id', 'file_path']
            )
        ],
        [
            pd.DataFrame(
                [
                    ['8e0a7079f73a4341398458351477c9edbbae2064', 'src/file_nm.cpp'],
                    ['ea39952af8fae82d98537a42e87be6f933468d4b', 'src/{ => module_nm}/file_nm.cpp'],
                    ['58dcfab39bb0d389e04a09fefb347395939af360', 'src/module_nm/file_nm.cpp'],
                ],
                columns = ['commit_id', 'file_path']
            ),
            pd.DataFrame(
                [
                    ['8e0a7079f73a4341398458351477c9edbbae2064', 'src/module_nm/file_nm.cpp'],
                    ['ea39952af8fae82d98537a42e87be6f933468d4b', 'src/module_nm/file_nm.cpp'],
                    ['58dcfab39bb0d389e04a09fefb347395939af360', 'src/module_nm/file_nm.cpp'],
                ],
                columns = ['commit_id', 'file_path']
            )
        ],
        [
            pd.DataFrame(
                [
                    ['8e0a7079f73a4341398458351477c9edbbae2064', 'src/file_nm_v0.cpp'],
                    ['ea39952af8fae82d98537a42e87be6f933468d4b', 'src/{file_nm_v0.cpp => file_nm_v1.cpp}'],
                    ['58dcfab39bb0d389e04a09fefb347395939af360', 'src/file_nm_v1.cpp'],
                    ['58dcfab39bb0d389e04a09fefb347395939af360', 'src/{file_nm_v1.cpp => file_nm_v2.cpp}'],
                    ['58dcfab39bb0d389e04a09fefb347395939af360', 'src/file_nm_v2.cpp'],
                ],
                columns = ['commit_id', 'file_path']
            ),
            pd.DataFrame(
                [
                    ['8e0a7079f73a4341398458351477c9edbbae2064', 'src/file_nm_v2.cpp'],
                    ['ea39952af8fae82d98537a42e87be6f933468d4b', 'src/file_nm_v2.cpp'],
                    ['58dcfab39bb0d389e04a09fefb347395939af360', 'src/file_nm_v2.cpp'],
                    ['58dcfab39bb0d389e04a09fefb347395939af360', 'src/file_nm_v2.cpp'],
                    ['58dcfab39bb0d389e04a09fefb347395939af360', 'src/file_nm_v2.cpp'],
                ],
                columns = ['commit_id', 'file_path']
            )
        ],
        [
            pd.DataFrame(
                [
                    ['8e0a7079f73a4341398458351477c9edbbae2064', 'Dockerfile_allbuild'],
                    ['ea39952af8fae82d98537a42e87be6f933468d4b', 'Dockerfile_allbuild => packaging/Dockerfile-allbuild'],
                    ['58dcfab39bb0d389e04a09fefb347395939af360', 'Dockerfile_allbuild => packaging/Dockerfile-allbuild'],
                    ['58dcfab39bb0d389e04a09fefb347395939af360', 'packaging/Dockerfile-allbuild'],
                ],
                columns = ['commit_id', 'file_path']
            ),
            pd.DataFrame(
                [
                    ['8e0a7079f73a4341398458351477c9edbbae2064', 'packaging/Dockerfile-allbuild'],
                    ['ea39952af8fae82d98537a42e87be6f933468d4b', 'packaging/Dockerfile-allbuild'],
                    ['58dcfab39bb0d389e04a09fefb347395939af360', 'packaging/Dockerfile-allbuild'],
                    ['58dcfab39bb0d389e04a09fefb347395939af360', 'packaging/Dockerfile-allbuild'],
                ],
                columns = ['commit_id', 'file_path']
            )
        ],
    ]

    ) # only relevant columns in input / expected for sake of simplicity
def test_handle_file_renaming(input_df, expected_df):

    obtained_df = handle_file_renaming(input_df)
    assert_frame_equal(obtained_df, expected_df)
