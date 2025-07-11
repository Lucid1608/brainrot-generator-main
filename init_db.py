from app import create_app, db
import os

app = create_app()
print(f"Current working directory: {os.getcwd()}")
print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")

with app.app_context():
    try:
        db.create_all()
        print('Database initialized!')
        print(f"Database file exists: {os.path.exists('app.db')}")
        print(f"Files in current directory: {os.listdir('.')}")
    except Exception as e:
        print(f"Error creating database: {e}")
        import traceback
        traceback.print_exc() 