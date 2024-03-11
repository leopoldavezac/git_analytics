
import os

from git_analytics.visualization import visualize
from git_analytics.config_management import ConfigManager

import git_analytics.utilities
import git_analytics.cmd_chaining
import git_analytics.git_log_parsing


def test_visualize(mocker):

    def run_server_mock(self):
        pass

    EXPECTED_OUTPUT_NMS = [
        '.gitignore',
        'random_reward_bot_clean_commits_files.parquet',
        'random_reward_bot_clean_commits.parquet',
        'random_reward_bot_raw_commits_files.csv',
        'random_reward_bot_raw_commits.csv'
        ].sort()

    config_manager = ConfigManager()
    config_manager.codebase_nm = 'random_reward_bot'
    config_manager.path_to_repo = "./test/asset/repo/RandomRewardBot"
    config_manager.src_path = './random_reward_bot'
    config_manager.module_depth = 1
    config_manager.component_nms = ['app', 'reward']
    config_manager.component_depth = 1
    config_manager.set_stats_template_from_file()

    mocker.patch.object(
        git_analytics.utilities,
        'DATA_PATH',
        './test/temp/data'
        )
    mocker.patch.object(
        git_analytics.cmd_chaining,
        'DATA_PATH',
        './test/temp/data'
        )
    mocker.patch.object(
        git_analytics.git_log_parsing,
        'DATA_PATH',
        './test/temp/data'
        )

    mocker.patch(
        'git_analytics.analysis.Dashboard.run_server',
        run_server_mock
    )

    os.system('unzip test/asset/repo.zip') #test repo is stored as zip to avoid maintaning two git repo

    visualize(config_manager)

    obtained_output_nms = os.listdir('./test/temp/data').sort()

    os.system('rm -R test/asset/repo')
    os.system('rm test/temp/data/*')

    assert obtained_output_nms == EXPECTED_OUTPUT_NMS
