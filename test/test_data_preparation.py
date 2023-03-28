import os

from numpy import nan
import pandas as pd

from pandas.testing import assert_frame_equal

import git_analytics.data_preparation
import git_analytics.utilities



def test_data_preparation(mocker): #integration_test

    mocker.patch.object(
        git_analytics.utilities,
        'CONFIG_PATH',
        './test/asset/config'
        )
    
    mocker.patch.object(
        git_analytics.utilities,
        'DATA_PATH',
        './test/temp/data'
        )

    EXPECTED_COMMITS = (
            pd.DataFrame(
                [
                    ['8e0a7079f73a4341398458351477c9edbbae2064', '2021-09-30 15:12:01 +0200', 'leopoldavezac','chore(rewards) - update yaml file', 0],
                    ['ea39952af8fae82d98537a42e87be6f933468d4b', '2021-09-30 15:04:49 +0200', 'leopoldavezac','chore(requirements) - none', 0],
                    ['58dcfab39bb0d389e04a09fefb347395939af360', '2021-09-30 15:03:45 +0200', 'leopoldavezac','refactor(app) - relative import', 1],
                    ['72a8f13827b42b2010098967533642b45e19bcd0', '2021-09-30 15:02:09 +0200', 'leopoldavezac','fix(rewards) - money as str', 0],
                    ['301c4e985455b96f1d6142642161716ba3130c73', '2021-09-29 15:58:58 +0200', 'leopoldavezac','chore(packaging) - install module for easy import', 17],
                    ['7f1a63ff379c0bd6a5cabc56dc46ab223e90d45e', '2021-09-29 15:58:07 +0200', 'leopoldavezac','chore(gitignore) - ignore cache and egg info', 0],
                    ['a2140d0462144ab0e58ee801a50b555fafde7a1f', '2021-09-29 15:56:31 +0200', 'leopoldavezac','feat(reward) - return (or not) reward to user', 35],
                    ['da89518e033844b5d1d7947fc9a407257f3c6184', '2021-09-29 15:35:08 +0200', 'leopoldavezac','refactoring(app) - renaming variables', 3],
                    ['4cc0ae168567f860bb58a1ac5d985e59d2ece5bd', '2021-09-29 14:23:08 +0200', 'leopoldavezac','feat(app) - return input msg as is', 20],
                    ['f44310f347a0144523c0393ab3fa217a907819d4', '2021-09-30 15:14:23 +0200', "leopold d'avezac",'Initial commit', 0],
                ],
                columns=['id', 'creation_dt', 'author_nm', 'msg', 'n_code_lines_inserted']
        )
        .astype({
            'id':'string',
            'author_nm':'category',
            'msg':'string',
            'n_code_lines_inserted':'uint32'
        })
        .assign(creation_dt = lambda dfx: pd.to_datetime(dfx.creation_dt, utc=True))
    )

    EXPECTED_COMMITS_FILES = (
            pd.DataFrame(
                [
                    ['8e0a7079f73a4341398458351477c9edbbae2064', '2021-09-30 15:12:01 +0200', 'leopoldavezac','rewards.yaml', 0, 0, 'other', False, nan],
                    ['ea39952af8fae82d98537a42e87be6f933468d4b', '2021-09-30 15:04:49 +0200', 'leopoldavezac','requirements.txt', 0, 0, 'other', False, nan],
                    ['58dcfab39bb0d389e04a09fefb347395939af360', '2021-09-30 15:03:45 +0200', 'leopoldavezac','random_reward_bot/app.py', 1, 1, 'py', True, 'app'],
                    ['58dcfab39bb0d389e04a09fefb347395939af360', '2021-09-30 15:03:45 +0200', 'leopoldavezac','setup.py', 0, 17, 'py', False, nan],
                    ['72a8f13827b42b2010098967533642b45e19bcd0', '2021-09-30 15:02:09 +0200', 'leopoldavezac','rewards.yaml', 0, 0, 'other', False, nan],
                    ['301c4e985455b96f1d6142642161716ba3130c73', '2021-09-29 15:58:58 +0200', 'leopoldavezac','setup.py', 17, 0, 'py', False, nan],
                    ['7f1a63ff379c0bd6a5cabc56dc46ab223e90d45e', '2021-09-29 15:58:07 +0200', 'leopoldavezac','.gitignore', 0, 0, 'other', False, nan],
                    ['a2140d0462144ab0e58ee801a50b555fafde7a1f', '2021-09-29 15:56:31 +0200', 'leopoldavezac','random_reward_bot/app.py', 6, 2, 'py', True, 'app'],
                    ['a2140d0462144ab0e58ee801a50b555fafde7a1f', '2021-09-29 15:56:31 +0200', 'leopoldavezac','random_reward_bot/rewards.py', 29, 0, 'py', True, 'rewards'],
                    ['a2140d0462144ab0e58ee801a50b555fafde7a1f', '2021-09-29 15:56:31 +0200', 'leopoldavezac','rewards.yaml', 0, 0, 'other', False, nan],
                    ['da89518e033844b5d1d7947fc9a407257f3c6184', '2021-09-29 15:35:08 +0200', 'leopoldavezac','random_reward_bot/app.py', 3, 3, 'py', True, 'app'],
                    ['4cc0ae168567f860bb58a1ac5d985e59d2ece5bd', '2021-09-29 14:23:08 +0200', 'leopoldavezac','random_reward_bot/app.py', 20, 0, 'py', True, 'app'],
                    ['f44310f347a0144523c0393ab3fa217a907819d4', '2021-09-30 15:14:23 +0200', "leopold d'avezac",'LICENSE', 0, 0, 'other', False, nan],
                    ['f44310f347a0144523c0393ab3fa217a907819d4', '2021-09-30 15:14:23 +0200', "leopold d'avezac",'README.md', 0, 0, 'other', False, nan],
                ],
                columns = ['commit_id', 'creation_dt', 'author_nm', 'file_nm', 'n_code_lines_inserted', 'n_code_lines_deleted', 'ext', 'is_src', 'module_nm']
        )
        .astype({
            'commit_id':'string',
            'author_nm':'category',
            'file_nm':'string',
            'n_code_lines_inserted':'uint32',
            'n_code_lines_deleted':'uint32',
            'ext':'category',
            'is_src':'bool',
            'module_nm':'category',
        })
        .assign(creation_dt = lambda dfx: pd.to_datetime(dfx.creation_dt, utc=True))
    .loc[:,['commit_id', 'file_nm', 'ext', 'is_src', 'module_nm', 'n_code_lines_inserted', 'n_code_lines_deleted', 'author_nm', 'creation_dt']]
    )


    os.system('unzip test/asset/repo.zip') #test repo is stored as zip to avoid maintaning two git repo

    git_analytics.data_preparation.main()

    obtained_commits = pd.read_parquet('./test/temp/data/commits.parquet')
    obtained_commits_files = pd.read_parquet('./test/temp/data/commits_files.parquet')
  
    assert_frame_equal(EXPECTED_COMMITS, obtained_commits)
    assert_frame_equal(EXPECTED_COMMITS_FILES, obtained_commits_files)

    os.system('rm -R test/asset/repo')