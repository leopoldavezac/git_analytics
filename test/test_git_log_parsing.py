from pandas import DataFrame
from pandas.testing import assert_frame_equal

from src.git_log_parsing import GitLogParser


def test_git_log_parsing():

    INPUT = """+++a2452407107a0c5a64e76cf422f4d6f788dcc814\t2019-05-30 12:26:49 +0200\tPHParo\tAdd README
1\t0\tREADME.md

+++a7a7d2e6067c97dd14be74b005909270e1858814\t2019-05-30 12:25:26 +0200\tPHParo\tDebug not found Icons lib + Display fatal erros + ignore functionalities
7\t0\t.gitignore
673\t0\tcomposer.lock
5\t5\tconfig.php
1\t1\tphpapp/admin/addons.php

+++ac945860b3f5eaf21ce65308ad2b33b475831041\t2019-03-21 10:55:33 +0100\tbaro\tReplace header('location:') by bab_redirect()
9\t16\tphpapp/admin/addons.php

+++47d8d655209ac82a4031d5000bc44223cea1cc8a\t2019-03-21 10:49:30 +0100\tbaro\tAdd bab_redirect() function
11\t0\tphpapp/utilit/addonapi.php
"""

    EXPECTED_COMMIT = DataFrame([
            ["a2452407107a0c5a64e76cf422f4d6f788dcc814", "2019-05-30 12:26:49 +0200", "PHParo", "Add README"],
            ["a7a7d2e6067c97dd14be74b005909270e1858814", "2019-05-30 12:25:26 +0200", "PHParo",  "Debug not found Icons lib + Display fatal erros + ignore functionalities"],
            ["ac945860b3f5eaf21ce65308ad2b33b475831041", "2019-03-21 10:55:33 +0100", "baro", "Replace header('location:') by bab_redirect()"],
            ["47d8d655209ac82a4031d5000bc44223cea1cc8a", "2019-03-21 10:49:30 +0100", "baro", "Add bab_redirect() function"],
        ],
        columns=['id', 'creation_dt', 'author_nm', 'msg']
    )

    EXPECTED_FILES = DataFrame([
            ["a2452407107a0c5a64e76cf422f4d6f788dcc814", "README.md", 1, 0],
            ["a7a7d2e6067c97dd14be74b005909270e1858814", ".gitignore", 7, 0],
            ["a7a7d2e6067c97dd14be74b005909270e1858814", "composer.lock", 673, 0],
            ["a7a7d2e6067c97dd14be74b005909270e1858814", "config.php", 5, 5],
            ["a7a7d2e6067c97dd14be74b005909270e1858814", "phpapp/admin/addons.php", 1, 1],
            ["ac945860b3f5eaf21ce65308ad2b33b475831041", "phpapp/admin/addons.php", 9, 16],
            ["47d8d655209ac82a4031d5000bc44223cea1cc8a", "phpapp/utilit/addonapi.php", 11, 0],
        ],
        columns=['commit_id', 'file_path', 'n_lines_inserted', 'n_lines_deleted']
    )

   
    parser = GitLogParser('None') # get log will not be used

    parser.parse_log(INPUT)
    obtained_df_commit, obtained_df_commit_file = parser.get_commit_as_dfs()

    assert_frame_equal(obtained_df_commit, EXPECTED_COMMIT)
    assert_frame_equal(obtained_df_commit_file, EXPECTED_FILES)


def test_handle_tab_in_commit_msg():

    INPUT = """+++a2452407107a0c5a64e76cf422f4d6f788dcc814\t2019-05-30 12:26:49 +0200\tPHParo\tAdd\tREADME\tphpapp
1\t0\tREADME.md
"""

    EXPECTED_COMMIT = DataFrame([
            ["a2452407107a0c5a64e76cf422f4d6f788dcc814", "2019-05-30 12:26:49 +0200", "PHParo", "Add README phpapp"],
        ],
        columns=['id', 'creation_dt', 'author_nm', 'msg']
    )

    parser = GitLogParser('None') # get log will not be used

    parser.parse_log(INPUT)
    obtained_df_commit, _ = parser.get_commit_as_dfs()

    assert_frame_equal(obtained_df_commit, EXPECTED_COMMIT)
