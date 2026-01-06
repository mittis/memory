"""Flask application factory for memory game."""
import sys
from pathlib import Path

from flask import Flask

# Ensure src directory is in Python path for imports
src_dir = Path(__file__).parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from config import config


def create_app(config_name: str = 'development') -> Flask:
    """Create and configure Flask application instance.

    Args:
        config_name: Environment configuration ('development', 'testing', 'production').
                    Defaults to 'development'.

    Returns:
        Configured Flask application instance.
    """
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config.from_object(config[config_name])

    # Register game blueprint
    from routes.game import game_bp  # pylint: disable=import-outside-toplevel
    app.register_blueprint(game_bp)

    return app


if __name__ == '__main__':
    import os
    app = create_app('development')
    # Allow environment variable override for port
    port = int(os.environ.get('FLASK_PORT', app.config['PORT']))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
