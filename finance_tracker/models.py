from flask_login import UserMixin
from . import db
from datetime import datetime

# Association table for many-to-many relationship between transactions and categories
transaction_categories = db.Table('transaction_categories',
    db.Column('transaction_id', db.Integer, db.ForeignKey('transaction.id'), primary_key=True),
    db.Column('category_id', db.Integer, db.ForeignKey('category.id'), primary_key=True)
)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)

    # Updated relationship to the new Transaction model
    transactions = db.relationship('Transaction', backref='user', lazy=True, cascade="all, delete-orphan")
    
    # New relationship to the Account model
    accounts = db.relationship('Account', backref='user', lazy=True, cascade="all, delete-orphan")
    
    categories = db.relationship('Category', backref='user', lazy=True, cascade="all, delete-orphan")
    budgets = db.relationship('Budget', backref='user', lazy=True, cascade="all, delete-orphan")

class Account(db.Model):
    __tablename__ = 'account'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    account_type = db.Column(db.String(50), nullable=False) # e.g., 'Checking', 'Savings', 'Credit Card'
    balance = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationship to transactions originating from this account
    transactions = db.relationship('Transaction', backref='account', lazy=True)

class Transaction(db.Model):
    __tablename__ = 'transaction'
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    
    # New column to distinguish between 'income' and 'expense'
    transaction_type = db.Column(db.String(20), nullable=False) 
    
    # Renamed from 'timestamp' for clarity
    transaction_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    description = db.Column(db.String(200), nullable=False)
    
    # New nullable text column for optional details
    notes = db.Column(db.Text, nullable=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # New Foreign Key to the Account model
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)

    # Updated relationship for many-to-many with Category
    categories = db.relationship('Category', secondary=transaction_categories, lazy='subquery',
                                 backref=db.backref('transactions', lazy=True))

class Category(db.Model):
    __tablename__ = 'category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    budgets = db.relationship('Budget', backref='category', lazy=True, cascade="all, delete-orphan")

class Budget(db.Model):
    __tablename__ = 'budget'
    id = db.Column(db.Integer, primary_key=True)
    month = db.Column(db.Integer, nullable=False) # Will store 1-12
    year = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)

    # This constraint prevents a user from creating more than one budget
    # for the same category in the same month and year.
    __table_args__ = (db.UniqueConstraint('user_id', 'category_id', 'month', 'year', name='_user_category_month_year_uc'),)