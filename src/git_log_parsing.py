from subprocess import run

from pandas import DataFrame

from src.config_management import instanciate_config_manager, ConfigManager

DATA_PATH = './data'

PRETTY_FORMAT = '+++%H\t%ad\t%an\t%s'
CMD_NM = 'parse_git'

class GitLogParser():


    def __init__(self, path_to_repo):

        self.path_to_repo = path_to_repo

    def __run_command(self, command):
        process = run(command.split(" "), capture_output=True)
        log = process.stdout.decode('utf-8')

        if process.returncode != 0:
            raise OSError(process.stderr.decode('utf-8'))

        return log
    
    def __get_log(self):

        command = "git -C %s log --all -M -C --numstat --date=iso --pretty=format:%s" % (
            self.path_to_repo, PRETTY_FORMAT
            )

        return self.__run_command(command)


    def __get_files_info(self, commit_id, commit_files_log):
                
        commit_files_log = commit_files_log[:-2]
        files_info = []

        for commit_file_log in commit_files_log:

            commit_file_log = commit_file_log.split('\t')

            if commit_file_log[0] == '-':
                nb_inserted_lines = 0
                nb_deleted_lines = 0
            else:
                nb_inserted_lines = int(commit_file_log[0])
                nb_deleted_lines = int(commit_file_log[1])

            files_info.append([
                commit_id,
                commit_file_log[2],
                nb_inserted_lines,
                nb_deleted_lines,
            ])

        return files_info

    def handle_tab_in_commit_msg(self, commit_info):

        commit_info[3] = ' '.join(commit_info[3:])
        commit_info = commit_info[:4]

        return commit_info

    def __parse_log(self, log:str) -> None:

        log = log.split('+++')[1:]
        
        log[-1] += '\n' #so last block can be dealt like the others ones

        self.commits = []
        self.commits_files = []

        for commit_log in log:

            commit_log = commit_log.split('\n')
            commit_info = commit_log[0].split('\t')

            if len(commit_info) > 4:
                commit_info = self.handle_tab_in_commit_msg(commit_info)

            commit_files_info = self.__get_files_info(commit_info[0], commit_log[1:])

            self.commits.append(commit_info)
            self.commits_files += commit_files_info

        self.df_commits = DataFrame(
            self.commits,
            columns=['id', 'creation_dt', 'author_nm', 'msg']
        )
        self.df_commits_files = DataFrame(
            self.commits_files,
            columns=['commit_id', 'file_nm', 'n_lines_inserted', 'n_lines_deleted']
        )


    def get_parsed_commits(self):
        try:
            return self.df_commits
        except AttributeError:
            self.__parse_log(self.__get_log())
            return self.df_commits

    def get_parsed_commits_files(self):

        try:
            return self.df_commits_files
        except AttributeError:
            self.__parse_log(self.__get_log())
            return self.df_commits_files


def parse_git_log(config_manager:ConfigManager) -> None:

    path_to_repo = config_manager['path_to_repo']
    git_log_parser = GitLogParser(path_to_repo)
    df_commits = git_log_parser.get_parsed_commits()
    df_commits_files = git_log_parser.get_parsed_commits_files()

    codebase_name = config_manager['codebase_nm']
    df_commits.to_csv('%s/%s_raw_commits.csv' % (DATA_PATH, codebase_name), index=False)
    df_commits_files.to_csv('%s/%s_raw_commits_files.csv' % (DATA_PATH, codebase_name), index=False)

def main() -> None:

    config_manager = instanciate_config_manager(CMD_NM)
    parse_git_log(config_manager)
    print('\nOK - git log of %s sucessfully parsed.\n' % config_manager['codebase_nm'])


if __name__ == '__main__': 
    main()
    