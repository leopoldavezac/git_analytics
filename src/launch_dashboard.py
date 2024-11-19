from src.visualization import visualize, CMD_NM
from src.config_management import instanciate_config_manager
from src.cmd_chaining import run_predecessor

def main() -> None:
    config_manager = instanciate_config_manager(CMD_NM)
    run_predecessor(CMD_NM, config_manager)

    web_app = visualize(config_manager)
    web_app.run_server()

# for debuger to works app must be accessible
if __name__ == '__main__':
    config_manager = instanciate_config_manager(CMD_NM)
    web_app = visualize(config_manager)
    app = web_app.app
    web_app.run_server()