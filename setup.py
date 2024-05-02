from setuptools import setup


setup(
    name='repo_health_analyzer',
    packages=['src'],
    entry_points = {
        'console_scripts': [
            'parse_git=src.git_log_parsing:main',
            'prep_data=src.data_preparation:main',
            'visualize=src.launch_dashboard:main',
            ],
    }
)         