
import os

from src.launch_dashboard import main as launch_dashboard
from src.config_management import ConfigManager

import src.utilities
import src.cmd_chaining
import src.git_log_parsing


def test_integration_visualize(mocker):

    def run_server_mock(self):
        pass

    EXPECTED_OUTPUT_NMS = [
        '.gitignore',
        'random_reward_bot_clean_commit_file.parquet',
        'random_reward_bot_clean_commit.parquet',
        'random_reward_bot_raw_commit_file.csv',
        'random_reward_bot_raw_commit.csv'
        ].sort()

    config_manager = ConfigManager()
    config_manager.codebase_nm = 'random_reward_bot'
    config_manager.path_to_repo = "./test/asset/repo/RandomRewardBot"
    config_manager.src_path = './random_reward_bot'
    config_manager.module_depth = 1
    config_manager.component_nms = ['app', 'reward']
    config_manager.component_depth = 1
    config_manager.has_components = True
    config_manager.set_dashboard_specs_from_config()

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

    mocker.patch(
        'src.visualization.Dashboard.run_server',
        run_server_mock
    )

    mocker.patch('src.launch_dashboard.instanciate_config_manager', return_value=config_manager)

    os.system('unzip test/asset/repo.zip') #test repo is stored as zip to avoid maintaning two git repo

    launch_dashboard()

    obtained_output_nms = os.listdir('./test/temp/data').sort()

    os.system('rm -R test/asset/repo')
    os.system('rm test/temp/data/*')

    assert obtained_output_nms == EXPECTED_OUTPUT_NMS
