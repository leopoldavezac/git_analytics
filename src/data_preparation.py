from os.path import join
import json

from pandas import to_datetime

from src.commit_files_tagging import CommitFilesTagger
from src.config_management import instanciate_config_manager
from src.cmd_chaining import run_predecessor
from src.utilities import read_raw, save_cleaned

CMD_NM = 'prep_data'

def apply_author_nm_merging(df_commit, codebase_nm):
    
    file_path = join('data', codebase_nm, 'author_nm_merging.json')

    try:
        with open(file_path) as f:
            author_nm_mapping = json.load(f)

    except FileNotFoundError:
        return df_commit
    
    except json.JSONDecodeError:
        raise ValueError("The file 'config/author_nm_merging.json' is not a valid JSON.")

    df_commit['author_nm'] = df_commit['author_nm'].replace(author_nm_mapping)

    return df_commit


def tag_commit_files(df_commit_files, config_manager):

    commits_files_tagger = CommitFilesTagger(
        config_manager['src_path'],
        config_manager['module_depth'],
        config_manager['component_nms'],
        config_manager['component_depth'],
        )
    
    df_commit_files = commits_files_tagger.tag_file_ext(df_commit_files)
    df_commit_files = commits_files_tagger.tag_src_file(df_commit_files)
    
    if config_manager['component_nms'] is not None:
       df_commit_files = commits_files_tagger.tag_component(df_commit_files)

    df_commit_files = commits_files_tagger.tag_module(df_commit_files)

    return df_commit_files


def handle_root_files(df_file_path_mapping):

    old_is_root_file_filter = (df_file_path_mapping.old == "") & (~df_file_path_mapping.prefix.str.contains('/'))

    df_file_path_mapping.loc[old_is_root_file_filter, 'old'] = df_file_path_mapping.loc[old_is_root_file_filter, 'prefix']
    df_file_path_mapping.loc[old_is_root_file_filter, 'prefix'] = ""

    return df_file_path_mapping


def set_new_file_path_on_update(df_commit_files, df_file_path_mapping):
    
    df_commit_files.loc[df_file_path_mapping.index, 'file_path'] = df_file_path_mapping.new.values

    return df_commit_files


def handle_multi_renaming(df_file_path_mapping):

    return (
        df_file_path_mapping
        .drop_duplicates()
        .merge(
            df_file_path_mapping,
            left_on='new',
            right_on='old',
            how='left'
        )
        .drop(columns='old_y')
        .rename(columns={'old_x':'old', 'new_x':'old_new', 'new_y':'new'})
        .assign(new = lambda dfy: dfy.new.fillna(dfy.old_new))
        [['old', 'new']]
    )


def get_mapping_as_dict(df_file_path_mapping):

    return {v[0]:v[1] for _, v in df_file_path_mapping.iterrows()}

# file path update not file renaming
def handle_file_renaming(df_commit_files):

    REGEX_FILE_PATH_UPDATE = r'([A-z\./0-9\-_]*){{0,1}([A-z\./0-9\-_]*) => ([A-z\./0-9\-_]*)}{0,1}([A-z\./0-9\-_]*)'

    filter_file_path_update = df_commit_files.file_path.str.contains(' => ')

    if filter_file_path_update.sum() == 0:
        return df_commit_files

    df_file_path_mapping = (
        df_commit_files
        .loc[filter_file_path_update]
        .pipe(lambda dfx: (
            dfx
            .file_path.str.extract(REGEX_FILE_PATH_UPDATE)
            .set_axis(['prefix', 'old', 'new', 'suffix'], axis=1)
        ))
    )

    df_file_path_mapping = handle_root_files(df_file_path_mapping)

    df_file_path_mapping = (
        df_file_path_mapping
        .assign(
            old = lambda dfx: (dfx.prefix + dfx.old + dfx.suffix).str.replace('//', '/'),
            new = lambda dfx: (dfx.prefix + dfx.new + dfx.suffix).str.replace('//', '/'),
        )
        [['old', 'new']]
    )

    df_commit_files = set_new_file_path_on_update(df_commit_files, df_file_path_mapping)

    df_file_path_mapping = handle_multi_renaming(df_file_path_mapping)

    file_path_mapping = get_mapping_as_dict(df_file_path_mapping)
    df_commit_files['file_path'] = df_commit_files.file_path.replace(file_path_mapping)

    return df_commit_files


def compute_n_code_lines(df_commit_files):

    for action_nm in ['inserted', 'deleted']:

        n_lines_action_nm = 'n_lines_%s' % action_nm
        n_code_lines_action_nm = 'n_code_lines_%s' % action_nm

        df_commit_files[n_code_lines_action_nm] = (
            df_commit_files[n_lines_action_nm].where(
                df_commit_files.ext != 'other', 0
            )
        )

    return df_commit_files


def denormalize(df_commit_files, df_commit, col_nms):

    return (
        df_commit_files
        .merge(
            df_commit[['id'] + col_nms],
            left_on = 'commit_id',
            right_on = 'id',
            how = 'left',
            validate='m:1'
        )
        .drop(columns='id')
    )


def cast_to_ref_types(df):

    VAR_NM_TO_REF_TYPE = {
        'id':'string',
        'creation_dt':'datetime69[ns]',
        'msg':'string',
        'author_nm':'string',
        'file_path':'string',
        'n_code_lines_inserted':'uint32',
        'n_code_lines_deleted':'uint32',
        'n_lines_inserted':'uint32',
        'n_lines_deleted':'uint32',
        'commit_id':'string',
        'ext':'string',
        'is_src':'bool',
        'is_test':'bool',
        'module_nm':'string',
        'component_nm':'string'
    }

    for col_nm in df.columns:

        if 'dt' in col_nm:
            df[col_nm] = to_datetime(df[col_nm], utc=True)
        else:
            df[col_nm] = df[col_nm].astype(VAR_NM_TO_REF_TYPE[col_nm])
    

    return df


def prepare_data(config_manager) -> None:
    
    df_commit = read_raw(config_manager['codebase_nm'], 'commits')
    df_commit = cast_to_ref_types(df_commit)
    df_commit = apply_author_nm_merging(df_commit, config_manager['codebase_nm'])
    
    df_commit_files = read_raw(config_manager['codebase_nm'], 'commits_files')
    df_commit_files = handle_file_renaming(df_commit_files)
    df_commit_files = tag_commit_files(df_commit_files, config_manager)
    df_commit_files = compute_n_code_lines(df_commit_files)    
    df_commit_files = denormalize(df_commit_files, df_commit, ['author_nm', 'creation_dt'])
    df_commit_files = cast_to_ref_types(df_commit_files)

    save_cleaned(df_commit, config_manager['codebase_nm'], 'commits')
    save_cleaned(df_commit_files, config_manager['codebase_nm'], 'commits_files')


def main() -> None:

    config_manager = instanciate_config_manager(CMD_NM)
    run_predecessor(CMD_NM, config_manager)

    prepare_data(config_manager)
    # not print but log
    print('\nOK - log data of %s has been sucessfully prepared.\n' % config_manager['codebase_nm'])


if __name__ == '__main__':
    prepare_data()