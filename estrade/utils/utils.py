import os
import yaml

import logging

logger = logging.getLogger(__name__)


def parse_yaml(config_file, key=None):
    if not os.path.isfile(config_file):
        logger.error('Configuration file not found: {}'.format(config_file))
        exit()

    with open(config_file, 'r') as f:
        data = yaml.safe_load(f)
        if key:
            return data[key]
        return data
