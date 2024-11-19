from subprocess import run

from pandas import DataFrame, concat

from src.config_management import instanciate_config_manager, ConfigManager

DATA_PATH = './data'
CMD_NM = 'parse_git'

class GitLogParser():

    COMMIT_FORMAT = '+++%H\t%ad\t%an\t%s'
    COMMIT_SEP = '+++'

    def __init__(self, path_to_repo):

        self.path_to_repo = path_to_repo

        self.df_commit = (
            DataFrame([], columns=['id', 'creation_dt', 'author_nm', 'msg'])
            .astype({'id':'str', 'creation_dt':'str', 'author_nm':'str', 'msg':'str'})
        )

        self.df_commit_files = (
            DataFrame(
                [],
                columns=['commit_id', 'file_path', 'n_lines_inserted', 'n_lines_deleted'],
            )
            .astype({'commit_id':'str', 'file_path':'str', 'n_lines_inserted':'int', 'n_lines_deleted':'int'})
        )

    def __run_command_in_cli(self, command):
        
        process = run(command.split(" "), capture_output=True)
        log = process.stdout.decode('utf-8')

        if process.returncode != 0:
            raise OSError(process.stderr.decode('utf-8'))

        return log
    
    def get_raw_log(self):
        
        command = f"git -C {self.path_to_repo} log --all -M -C --numstat --date=iso --pretty=format:{self.COMMIT_FORMAT}"
        
        return self.__run_command_in_cli(command)

    def __cast_to_int(self, n_lines):

        return 0 if n_lines == '-' else int(n_lines)

    def __parse_files_info(self, commit_id, files_info):
  
        files_info = files_info[:-2] #remove commit end msg character

        for i, info in enumerate(files_info):
            
            info = info.split('\t')

            nb_inserted_lines, nb_deleted_lines, file_path = info

            nb_inserted_lines = self.__cast_to_int(nb_inserted_lines)
            nb_deleted_lines = self.__cast_to_int(nb_deleted_lines)

            files_info[i] = [commit_id, file_path, nb_inserted_lines, nb_deleted_lines]

        return files_info

    def __handle_tab_in_msg(self, header):

        header[3] = ' '.join(header[3:])
        header = header[:4]

        return header
    
    def __format_files_info_as_df(self, files_info):

        self.df_commit_files = concat([
            self.df_commit_files,
            DataFrame(files_info, columns=self.df_commit_files.columns)
        ], axis=0, ignore_index=True)

    def parse_log(self, log:str) -> None:

        log = log.split(self.COMMIT_SEP)[1:] # remove empty first element -> cf self.pretty_format

        log[-1] += '\n' #update last commit to keep the same structure as other commits 

        files_info = []

        for commit in log:

            commit = commit.split('\n')
            header = commit[0].split('\t')
            commit_files_info = commit[1:]
            
            header_nb_attributes = 4
            if len(header) > header_nb_attributes:
                header = self.__handle_tab_in_msg(header)
            
            self.df_commit.loc[len(self.df_commit),:] = header

            commit_files_info = self.__parse_files_info(header[0], commit_files_info)
            files_info += commit_files_info
        
        self.__format_files_info_as_df(files_info)

    def get_commit_as_dfs(self): 

        return self.df_commit, self.df_commit_files


def parse_git_log(config_manager:ConfigManager) -> None:

    git_log_parser = GitLogParser(config_manager['path_to_repo'])
    log = git_log_parser.get_raw_log()
    git_log_parser.parse_log(log)
    df_commit, df_commit_files = git_log_parser.get_commit_as_dfs()

    codebase_name = config_manager['codebase_nm']
    df_commit.to_csv('%s/%s_raw_commits.csv' % (DATA_PATH, codebase_name), index=False)
    df_commit_files.to_csv('%s/%s_raw_commits_files.csv' % (DATA_PATH, codebase_name), index=False)

def main() -> None:

    config_manager = instanciate_config_manager(CMD_NM)
    parse_git_log(config_manager)
    # not print but log
    print('\nOK - git log of %s sucessfully parsed.\n' % config_manager['codebase_nm'])


if __name__ == '__main__': 
    main()
    