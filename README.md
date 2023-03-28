# Git Analytics


## Installation

```
conda env create -f env.yaml
conda active git_analytics
pip install -e .
```

## Execution

Run one of the following command with the required arguments : **parse_git**, **prep_data**, **analyze**. To know more on the different command just run 

```
<command> -h
```

For example,

```
parse_git -h
usage: parse_git [-h] codebase_nm path_to_repo

parse the git log of a codebase into a tabular format.

positional arguments:
  codebase_nm   identifier for the the codebase for which you wanna parse the git
  path_to_repo  local path to the codebase repository

options:
  -h, --help    show this help message and exit
```