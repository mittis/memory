"""Application configuration management."""
import json
from pathlib import Path


def load_config() -> dict:
    """Load configuration from config.json file.

    Returns:
        dict: Configuration dictionary with sensible defaults if file is unavailable.
    """
    config_file = Path(__file__).parent.parent / 'config.json'

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Fallback defaults for development
        return {
            'grid': '2x2',
            'gridOptions': {
                '2x2': {'width': 2, 'height': 2},
                '4x3': {'width': 4, 'height': 3},
                '6x5': {'width': 6, 'height': 5}
            }
        }


# Load configuration at startup
_loaded_config = load_config()
_selected_grid = _loaded_config.get('grid', '2x2')
_grid_options = _loaded_config.get('gridOptions', {})
_grid_settings = _grid_options.get(_selected_grid, _grid_options.get('2x2', {}))


class Config:
    """Base application configuration."""

    SECRET_KEY = 'dev-secret-key-change-in-production'
    PORT = _loaded_config.get('port', 8080)
    BOARD_WIDTH = _grid_settings.get('width', 2)
    BOARD_HEIGHT = _grid_settings.get('height', 2)
    TOTAL_PAIRS = (BOARD_WIDTH * BOARD_HEIGHT) // 2


class DevelopmentConfig(Config):
    """Development environment configuration."""

    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    """Testing environment configuration."""

    DEBUG = True
    TESTING = True


class ProductionConfig(Config):
    """Production environment configuration."""

    DEBUG = False
    TESTING = False


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
