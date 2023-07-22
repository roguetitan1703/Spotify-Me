import sys
import os

# Get the absolute path to the project's root directory
project_root = os.getcwd()
# print(f'Project root: {project_root}')
# Add the project's root directory to the Python path
sys.path.append(f'{project_root}/data')
sys.path.append(f'{project_root}/libs')

from spotify_ import api_helper, player_utils

player_utils.status_monitor(4)
