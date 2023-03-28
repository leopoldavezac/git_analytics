from git_analytics.analysis import analyze, CMD_NM
from git_analytics.config_management import instanciate_config_manager


config_manager = instanciate_config_manager(CMD_NM)
web_app = analyze(config_manager)
server = web_app.get_app_server()

if __name__ == '__main__':
    web_app.run_server()
