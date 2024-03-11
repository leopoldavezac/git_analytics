from setuptools import setup


setup(
    name='git_analytics',
    packages=['git_analytics'],
    entry_points = {
        'console_scripts': [
            'parse_git=git_analytics.git_log_parsing:main',
            'prep_data=git_analytics.data_preparation:main',
            'visualize=git_analytics.launch_dashboard:main',
            ],
    }
)         