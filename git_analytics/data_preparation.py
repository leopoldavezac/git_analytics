from git_analytics.git_log_parsing import GitLogParser
from git_analytics.commit_files_tagging import CommitFilesTagger
from git_analytics.utilities import (
    load_config,
    add_agg_column_on_id,
    denormalize_cols_on_id,
    update_with_ref_types,
    save_as_parquet,
    handle_file_renaming,
    get_n_code_lines_only,
)

def main():

    config = load_config('repo')

    git_log_parser = GitLogParser(config['path'])
    df_commits = git_log_parser.get_commits_info()
    df_commits_files = git_log_parser.get_commits_files_info()
    
    df_commits_files = handle_file_renaming(df_commits_files)

    commits_files_tagger = CommitFilesTagger(df_commits_files, config['repo_struct'])
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

    save_as_parquet(df_commits, 'commits')
    save_as_parquet(df_commits_files, 'commits_files')


if __name__ == '__main__':

    main()