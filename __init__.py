import rodan
from rodan.jobs import module_loader
import logging

__version__ = "0.1.0"
logger = logging.getLogger('rodan')
module_loader('rodan.jobs.JSOMR2MEI')
