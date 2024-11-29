from os import listdir

from src.config_management import ConfigManager

DATA_PATH = './data'

CMD_NM_TO_PRECURSOR_CMD_NM = {
    'visualize':'prep_data',
    'prep_data':'parse_git',
    'parse_git':None
}

CMD_NM_TO_OUTPUT_FORMAT = {
    'parse_git':'%s_raw_commit.csv',
    'prep_data':'%s_clean_commit.parquet'
}


def map_cmd_to_func(cmd_nm:str): #to avoid circular import

    if cmd_nm == 'parse_git':
        from src.git_log_parsing import parse_git_log
        return parse_git_log
    elif cmd_nm == 'prep_data':
        from src.data_preparation import prepare_data
        return prepare_data
        
def run_cmd(cmd_nm:str, config_manager:ConfigManager) -> None:

    cmd_func = map_cmd_to_func(cmd_nm)

    if not config_manager.check_completion_for(cmd_nm):
        raise ValueError(f'Insuficent arguments for running {cmd_nm}.')
    else:
        cmd_func(config_manager)

def check_if_command_has_run(cmd_nm, codebase_nm):

    cmd_output_nm = CMD_NM_TO_OUTPUT_FORMAT[cmd_nm] % codebase_nm

    return cmd_output_nm in listdir(DATA_PATH)

def run_predecessor(cmd_nm, config_manager, first_cmd=True) -> None:
    precursor_cmd_nm = CMD_NM_TO_PRECURSOR_CMD_NM.get(cmd_nm)

    if precursor_cmd_nm is None:  
        run_cmd(cmd_nm, config_manager)
    else:
        if config_manager['rerun'] or not check_if_command_has_run(precursor_cmd_nm, config_manager['codebase_nm']):
            run_predecessor(precursor_cmd_nm, config_manager, first_cmd=False)  

        if first_cmd == False:
            run_cmd(cmd_nm, config_manager)