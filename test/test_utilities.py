

from pandas import DataFrame
from pandas.testing import assert_frame_equal

from git_analytics.utilities import handle_file_renaming

import pytest


@pytest.mark.parametrize(
    'input_df,expected_df',
    [
        [
            DataFrame(
                [
                    ['8e0a7079f73a4341398458351477c9edbbae2064', 'src/old_file_nm.cpp'],
                    ['ea39952af8fae82d98537a42e87be6f933468d4b', 'src/{old_file_nm.cpp => new_file_nm.cpp}'],
                    ['58dcfab39bb0d389e04a09fefb347395939af360', 'src/new_file_nm.cpp'],
                ],
                columns = ['commit_id', 'file_nm']
            ),
            DataFrame(
                [
                    ['8e0a7079f73a4341398458351477c9edbbae2064', 'src/new_file_nm.cpp'],
                    ['ea39952af8fae82d98537a42e87be6f933468d4b', 'src/new_file_nm.cpp'],
                    ['58dcfab39bb0d389e04a09fefb347395939af360', 'src/new_file_nm.cpp'],
                ],
                columns = ['commit_id', 'file_nm']
            )
        ],
        [
            DataFrame(
                [
                    ['8e0a7079f73a4341398458351477c9edbbae2064', 'src/file_nm.cpp'],
                    ['ea39952af8fae82d98537a42e87be6f933468d4b', 'src/{ => module_nm}/file_nm.cpp'],
                    ['58dcfab39bb0d389e04a09fefb347395939af360', 'src/module_nm/file_nm.cpp'],
                ],
                columns = ['commit_id', 'file_nm']
            ),
            DataFrame(
                [
                    ['8e0a7079f73a4341398458351477c9edbbae2064', 'src/module_nm/file_nm.cpp'],
                    ['ea39952af8fae82d98537a42e87be6f933468d4b', 'src/module_nm/file_nm.cpp'],
                    ['58dcfab39bb0d389e04a09fefb347395939af360', 'src/module_nm/file_nm.cpp'],
                ],
                columns = ['commit_id', 'file_nm']
            )
        ],
        [
            DataFrame(
                [
                    ['8e0a7079f73a4341398458351477c9edbbae2064', 'src/file_nm_v0.cpp'],
                    ['ea39952af8fae82d98537a42e87be6f933468d4b', 'src/{file_nm_v0.cpp => file_nm_v1.cpp}'],
                    ['58dcfab39bb0d389e04a09fefb347395939af360', 'src/file_nm_v1.cpp'],
                    ['58dcfab39bb0d389e04a09fefb347395939af360', 'src/{file_nm_v1.cpp => file_nm_v2.cpp}'],
                    ['58dcfab39bb0d389e04a09fefb347395939af360', 'src/file_nm_v2.cpp'],
                ],
                columns = ['commit_id', 'file_nm']
            ),
            DataFrame(
                [
                    ['8e0a7079f73a4341398458351477c9edbbae2064', 'src/file_nm_v2.cpp'],
                    ['ea39952af8fae82d98537a42e87be6f933468d4b', 'src/file_nm_v2.cpp'],
                    ['58dcfab39bb0d389e04a09fefb347395939af360', 'src/file_nm_v2.cpp'],
                    ['58dcfab39bb0d389e04a09fefb347395939af360', 'src/file_nm_v2.cpp'],
                    ['58dcfab39bb0d389e04a09fefb347395939af360', 'src/file_nm_v2.cpp'],
                ],
                columns = ['commit_id', 'file_nm']
            )
        ],
        [
            DataFrame(
                [
                    ['8e0a7079f73a4341398458351477c9edbbae2064', 'Dockerfile_allbuild'],
                    ['ea39952af8fae82d98537a42e87be6f933468d4b', 'Dockerfile_allbuild => packaging/Dockerfile-allbuild'],
                    ['58dcfab39bb0d389e04a09fefb347395939af360', 'Dockerfile_allbuild => packaging/Dockerfile-allbuild'],
                    ['58dcfab39bb0d389e04a09fefb347395939af360', 'packaging/Dockerfile-allbuild'],
                ],
                columns = ['commit_id', 'file_nm']
            ),
            DataFrame(
                [
                    ['8e0a7079f73a4341398458351477c9edbbae2064', 'packaging/Dockerfile-allbuild'],
                    ['ea39952af8fae82d98537a42e87be6f933468d4b', 'packaging/Dockerfile-allbuild'],
                    ['58dcfab39bb0d389e04a09fefb347395939af360', 'packaging/Dockerfile-allbuild'],
                    ['58dcfab39bb0d389e04a09fefb347395939af360', 'packaging/Dockerfile-allbuild'],
                ],
                columns = ['commit_id', 'file_nm']
            )
        ],
    ]

    ) # only relevant columns in input / expected for sake of simplicity
def test_handle_file_renaming(input_df, expected_df):

    obtained_df = handle_file_renaming(input_df)
    assert_frame_equal(obtained_df, expected_df)