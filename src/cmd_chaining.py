from os import listdir

from src.config_management import ConfigManager

DATA_PATH = './data'

CMD_NM_TO_PRECURSOR_CMD_NM = {
    'visualize':'prep_data',
    'prep_data':'parse_git'
}

CMD_NM_TO_OUTPUT_FORMAT = {
    'parse_git':'%s_raw_commits.csv',
    'prep_data':'%s_clean_commits.parquet'
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
        raise ValueError('Insuficent arguments for running %s.' % cmd_nm)
    else:
        cmd_func(config_manager)

def command_has_run(cmd_nm, codebase_nm):

    cmd_output_nm = CMD_NM_TO_OUTPUT_FORMAT[cmd_nm] % codebase_nm

    return cmd_output_nm in listdir(DATA_PATH)

def run_predessor_if_needed(cmd_nm:str, config_manager:ConfigManager) -> None:

    precursor_cmd_nm = CMD_NM_TO_PRECURSOR_CMD_NM[cmd_nm]
        
    if config_manager['rerun']:
        run_cmd(precursor_cmd_nm, config_manager)
    else:
        if not command_has_run(precursor_cmd_nm, config_manager['codebase_nm']):
            run_cmd(precursor_cmd_nm, config_manager)
            
