"""
Setup for Semantic Kernel framework.

This module provides proxy imports for the Semantic Kernel factory functions,
which have been moved to konveyor.core.kernel.
"""

import logging

from konveyor.core.kernel import create_kernel, get_kernel_settings

# Configure logging
logger = logging.getLogger(__name__)
logger.info("Using create_kernel and get_kernel_settings from konveyor.core.kernel")
