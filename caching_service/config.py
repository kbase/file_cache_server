"""All global application configuration data."""
import os


class Config:
    """Basic global application configuration."""

    package_dir = os.path.dirname(__file__)
    base_dir = os.path.abspath(os.path.join(package_dir, '..'))
    secret_key = os.environ['SECRET_KEY']
