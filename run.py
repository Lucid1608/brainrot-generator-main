from app import create_app, db
from models import User

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User}

@app.cli.command()
def init_db():
    """Initialize the database."""
    db.create_all()
    print('Database initialized!')

@app.cli.command()
def create_admin():
    """Create an admin user."""
    email = input('Enter admin email: ')
    password = input('Enter admin password: ')
    
    user = User()
    user.email = email
    user.username = email.split('@')[0]  # Use email prefix as username
    user.is_verified = True
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    print(f'Admin user {email} created!')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 