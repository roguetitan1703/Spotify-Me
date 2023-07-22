import logging
import os
import colorlog

class log_helper:

    def __init__(self, log_file, log_level='DEBUG', debug_mode=False):
        self.log_path = f'{os.getcwd()}/logs'
        self.log_file = f'{self.log_path}/{log_file}'
        self.log_level = log_level.upper()
        self.debug_mode = debug_mode
        self.logger = colorlog.getLogger()
        self.logger.setLevel(logging.getLevelName(self.log_level))

        self.setup_file_handler()
        if not self.debug_mode:
            self.clear_log_file()
            self.log_message('info', 'Starting Program')

    def setup_file_handler(self):
        # Create a FileHandler to save log messages into a .log file
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.DEBUG)

        # Create a formatter for the file handler
        formatter = colorlog.ColoredFormatter(
            '%(asctime)s - %(log_color)s%(levelname)-8s%(reset)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        )
        file_handler.setFormatter(formatter)

        # Add the file handler to the logger
        self.logger.addHandler(file_handler)

    def log_message(self, log_level, message):
        # Validate the log level provided by the user
        log_level = log_level.upper()
        if log_level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            raise ValueError("Invalid log level. Expected one of: DEBUG, INFO, WARNING, ERROR, CRITICAL")

        # Mapping log levels to corresponding logging methods
        log_level_mapping = {
            'DEBUG': self.logger.debug,
            'INFO': self.logger.info,
            'WARNING': self.logger.warning,
            'ERROR': self.logger.error,
            'CRITICAL': self.logger.critical
        }

        # Log the message with the specified log level using the mapped logging method
        log_level_mapping[log_level](message)

    def read_log_file(self):
        # Read and display the contents of the log file line by line
        with open(self.log_file, 'r') as file:
            for line in file:
                line = line.strip()  # To remove any leading/trailing whitespace
                print(line)

    def clear_log_file(self):
        with open(self.log_file, 'w') as file:
            # Opening the file in 'w' mode truncates it, effectively clearing its contents.
            pass

if __name__ == '__main__':
    log_file_name = input('Enter the log file name (e.g., filename.log): ')
    logger = log_helper(log_file=log_file_name, debug_mode=True)

    logger.read_log_file()
