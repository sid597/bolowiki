# Python packages
import logging
from pprint import pprint

# External Packages
from flask_migrate import Migrate
from flask import Flask
from dotenv import load_dotenv
from os.path import join, dirname
# from flask import current_app as app

# Local Packages
from bolowikiApp.models import db
from bolowikiApp.config import Config


migrate = Migrate()

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)


def create_app(config_class=Config):
    app = Flask(__name__, template_folder='templates')
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)

    from bolowikiApp.Users.routes import users_bp
    from bolowikiApp.main.routes import main_bp
    from bolowikiApp.wikipedia_text_to_speech.routes import textToSpeech_bp
    from bolowikiApp.Translate.routes import translate_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(translate_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(textToSpeech_bp)

    return app


this_app = create_app()

if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    this_app.logger.handlers = gunicorn_logger.handlers
    this_app.logger.setLevel(gunicorn_logger.level)
if __name__ == '__main__':
    this_app.run(debug=True)
