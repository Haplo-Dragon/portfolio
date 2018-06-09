from flask import Flask, render_template
from flask_scss import Scss
import lament_mod.lament as lament


def create_app():
    app = Flask(__name__)
    app.config.from_object(__name__)

    app.config['DEBUG'] = False
    app.config['SECRET_KEY'] = 'devkey devkey'

    # Parse SCSS styling into CSS
    scss = Scss(app)
    scss.update_scss()

    # Register blueprints
    app.register_blueprint(lament.lamentApp)

    @app.route('/')
    def index():
        return render_template('portfolio.html', title="Ethan Fulbright")

    @app.after_request
    def gnu_terry_pratchett(resp):
        resp.headers.add("X-Clacks-Overhead", "GNU Terry Pratchett")
        return resp

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(port=42000)
