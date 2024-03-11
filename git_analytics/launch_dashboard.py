from git_analytics.visualization import visualize, CMD_NM
from git_analytics.config_management import instanciate_config_manager

def main() -> None:
    config_manager = instanciate_config_manager(CMD_NM)
    web_app = visualize(config_manager)
    web_app.run_server()

if __name__ == '__main__':
    main()
