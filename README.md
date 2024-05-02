# Repo Health Analyzer

Repo Heath Analyzer is the tool for assesing a codebase perinity in minutes using just the git log.

What you can do with this tool :

- Find out which developper is key : who has knowledge of what
- Learns about past activity : what are the stable parts of the code what are the moving parts

You can also use it to just parse a git log into a nice format for your data analysis.

Special thanks to @er-vin for which work on ComDaAn from which I have draw inspiration.

## Installation

You need python & virtualenv to install this tool.

```
virtualenv venv --python=python3.10
source venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

## Execution

Run one of the following command with the required arguments : **parse_git**, **prep_data**, **visualize**. To know more on the different command just run 

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

The three commands works sequentially and depend on each other, prep_data expect a passed execution of parse_git and visualize of the others two.
You can either run them one by one or directly run visualize and pass it all the required arguments for parse_git & prep_data.

## Key concepts

In order to help you analyze the git log of your codebase, Repo Health Analyzer assume that your codebase is organized in modules & components. 

- Module : Modules definition depend on the codebase file structure they can be file or directory. In the example, of an e-commerce web site modules might be : products, search, checkout etc.
- Component : (optionnal) Component is another axis of structure of your code that is shared accross module. If we take again the e-commerce example component might be : view, control, model.

## Correcting git log data

If you need to make corrections to your data (ex: exclude a file or a period) you can do so by directly updating the <codebase>_clean_commits.parquet & <codebase>_clean_commits_files.parquet. Make sure you don't alter the files format.