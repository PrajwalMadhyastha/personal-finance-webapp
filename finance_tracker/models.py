# finance_tracker/models.py
from . import db, bcrypt
from datetime import datetime
from flask_login import UserMixin

# --- NEW Category Model ---
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    
    # Foreign key to link to the user who created this category
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # This relationship links a category back to all expenses that use it
    expenses = db.relationship('Expense', backref='category', lazy=True)

    def __repr__(self):
        return f'<Category {self.name}>'


class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Link to the user who owns this expense
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # --- CHANGE: Replace category string with a foreign key ---
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)

    def __repr__(self):
        return f'<Expense ID: {self.id}, Desc: {self.description}>'


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    # Relationship to expenses this user owns
    expenses = db.relationship('Expense', backref='owner', lazy=True)
    
    # --- ADD THIS RELATIONSHIP ---
    # Relationship to categories this user has created
    categories = db.relationship('Category', backref='creator', lazy=True)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'