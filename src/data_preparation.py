from src.commit_files_tagging import CommitFilesTagger
from src.config_management import ConfigManager, instanciate_config_manager
from src.cmd_chaining import run_predessor_if_needed
from src.utilities import (
    get_parsed_git_log,
    add_agg_column_on_id,
    denormalize_cols_on_id,
    update_with_ref_types,
    save_as_parquet,
    handle_file_renaming,
    get_n_code_lines_only,
    AuthorNameGrouper
)

CMD_NM = 'prep_data'

def prepare_data(config_manager:ConfigManager) -> None:

    run_predessor_if_needed(CMD_NM, config_manager)

    df_commits = get_parsed_git_log(config_manager['codebase_nm'], 'commits')
    df_commits_files = get_parsed_git_log(config_manager['codebase_nm'], 'commits_files')

    author_nm_grouper = AuthorNameGrouper()
    author_nm_grouper.fit(df_commits.author_nm)
    df_commits['author_nm'] = author_nm_grouper.transform(df_commits.author_nm)   

    df_commits_files = handle_file_renaming(df_commits_files)

    src_path = config_manager['src_path']
    module_depth = config_manager['module_depth']
    component_nms = config_manager['component_nms']
    component_depth = config_manager['component_depth']

    commits_files_tagger = CommitFilesTagger(
        df_commits_files,
        src_path,
        module_depth,
        component_nms,
        component_depth
        )
    df_commits_files = commits_files_tagger.get_tagged_files()

    df_commits_files = get_n_code_lines_only(df_commits_files)    

    df_commits = add_agg_column_on_id(
        df_commits,
        df_commits_files,
        'sum',
        'n_code_lines_inserted'
    )

    df_commits_files = denormalize_cols_on_id(
        df_commits_files,
        df_commits,
        ['author_nm', 'creation_dt']
    )

    df_commits = update_with_ref_types(df_commits)
    df_commits_files = update_with_ref_types(df_commits_files)

    save_as_parquet(df_commits, config_manager['codebase_nm'], 'commits')
    save_as_parquet(df_commits_files, config_manager['codebase_nm'], 'commits_files')


def main() -> None:
    config_manager = instanciate_config_manager(CMD_NM)
    prepare_data(config_manager)
    print('\nOK - log data of %s has been sucessfully prepared.\n' % config_manager['codebase_nm'])


if __name__ == '__main__':
    main()
   