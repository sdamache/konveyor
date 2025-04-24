#!/bin/bash

# Remove asyncio package from site-packages to prevent conflicts with the built-in asyncio module
echo "Removing asyncio package from site-packages..."
find /home/site/wwwroot/.python_packages -name asyncio -type d -exec rm -rf {} \; 2>/dev/null
find /home/site/wwwroot/.python_packages -name "asyncio*.egg-info" -type d -exec rm -rf {} \; 2>/dev/null

# Continue with normal startup
exec "$@"
