from subprocess import run

from pandas import DataFrame

PRETTY_FORMAT = '+++%H\t%ad\t%an\t%s'

class GitLogParser():


    def __init__(self, path_to_dir):

        self.path_to_dir = path_to_dir

    def __run_command(self, command):
        process = run(command.split(" "), capture_output=True)
        log = process.stdout.decode('utf-8')

        if process.returncode != 0:
            raise OSError(process.stderr.decode('utf-8'))

        return log
    
    def __get_log(self):

        command = "git -C %s log --all -M -C --numstat --date=iso --pretty=format:%s" % (self.path_to_dir, PRETTY_FORMAT)

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
        self.files = []

        for commit_log in log:

            commit_log = commit_log.split('\n')
            commit_info = commit_log[0].split('\t')

            if len(commit_info) > 4:
                commit_info = self.handle_tab_in_commit_msg(commit_info)

            commit_files_info = self.__get_files_info(commit_info[0], commit_log[1:])

            self.commits.append(commit_info)
            self.files += commit_files_info

        self.commits = DataFrame(
            self.commits,
            columns=['id', 'creation_dt', 'author_nm', 'msg']
        )
        self.files = DataFrame(
            self.files,
            columns=['commit_id', 'file_nm', 'n_lines_inserted', 'n_lines_deleted']
        )


    def get_commits_info(self):
        try:
            return self.commits
        except AttributeError:
            self.__parse_log(self.__get_log())
            return self.commits

    def get_commits_files_info(self):

        try:
            return self.files
        except AttributeError:
            self.__parse_log(self.__get_log())
            return self.files


    