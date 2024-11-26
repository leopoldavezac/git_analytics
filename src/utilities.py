from os.path import join

from yaml import load, FullLoader

from pandas import (
    read_parquet,
    DataFrame, 
    read_csv
)

VAR_NM_TO_REF_TYPE = {
    'id':'string',
    'creation_dt':'datetime69[ns]',
    'msg':'string',
    'author_nm':'string',
    'file_nm':'string',
    'n_lines_inserted':'uint32',
    'n_lines_deleted':'uint32',
    'commit_id':'string',
    'ext':'string',
    'is_src':'bool',
    'is_test':'bool',
    'module_nm':'string',
    'component_nm':'string'
}

DATA_PATH = './data'
CONFIG_PATH = './config'


def read_raw(codebase_nm:str, log_level:str) -> DataFrame:
    
    file_path = join(DATA_PATH, f'{codebase_nm}_raw_{log_level}.csv')
    return read_csv(file_path)


def save_raw(df:DataFrame, codebase_nm:str, log_level:str) -> DataFrame:
    
    file_path = join(DATA_PATH, f'{codebase_nm}_raw_{log_level}.csv')
    df.to_csv(file_path, index=False)

def save_cleaned(df:DataFrame, codebase_nm:str, log_level:str) -> None:

    file_path = join(DATA_PATH, f'{codebase_nm}_clean_{log_level}.parquet')
    df.to_parquet(file_path, engine='pyarrow', version="2.4")


def read_cleaned(codebase_nm:str, log_level:str) -> DataFrame:

    file_path = join(DATA_PATH, f'{codebase_nm}_clean_{log_level}.parquet')
    df = read_parquet(file_path, engine='pyarrow')

    return df.set_index('creation_dt')


def load_config(scope_nm):

    file_path = join(CONFIG_PATH, f'{scope_nm}.yaml')

    with open(file_path, 'r') as f:
        config = load(f, Loader=FullLoader)

    return config