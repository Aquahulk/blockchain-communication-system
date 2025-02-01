from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'e187eb5382610cda775c8679351720cc143400548c174050cea779eec6d3f811'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
    
    # Initialize extensions with the app
    db.init_app(app)
    login_manager.init_app(app)
    
    # Import routes after the app is created to avoid circular imports
    from app.routes import main
    app.register_blueprint(main)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app

# Create the app instance
app = create_app()



