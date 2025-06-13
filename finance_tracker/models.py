from flask_login import UserMixin
from . import db
from datetime import datetime

transaction_tags = db.Table('transaction_tags',
    db.Column('transaction_id', db.Integer, db.ForeignKey('transaction.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

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
    transactions = db.relationship('Transaction', backref='user', lazy=True, cascade="all, delete-orphan")
    accounts = db.relationship('Account', backref='user', lazy=True, cascade="all, delete-orphan")
    
    categories = db.relationship('Category', backref='user', lazy=True, cascade="all, delete-orphan")
    budgets = db.relationship('Budget', backref='user', lazy=True, cascade="all, delete-orphan")
    tags = db.relationship('Tag', backref='user', lazy=True, cascade="all, delete-orphan")
    recurring_transactions = db.relationship('RecurringTransaction', backref='user', lazy=True, cascade="all, delete-orphan")

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
    transaction_type = db.Column(db.String(20), nullable=False) 
    transaction_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    description = db.Column(db.String(200), nullable=False)
    notes = db.Column(db.Text, nullable=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    categories = db.relationship('Category', secondary=transaction_categories, lazy='subquery',
                                 backref=db.backref('transactions', lazy=True))
    tags = db.relationship('Tag', secondary=transaction_tags, lazy='subquery',
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

class Tag(db.Model):
    __tablename__ = 'tag'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Ensures a user cannot have two tags with the same name (case-insensitive)
    __table_args__ = (db.UniqueConstraint('user_id', 'name', name='_user_tag_name_uc'),)

class RecurringTransaction(db.Model):
    __tablename__ = 'recurring_transaction'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # 'income' or 'expense'
    
    # How often the transaction occurs
    recurrence_interval = db.Column(db.String(50), nullable=False) # e.g., 'daily', 'weekly', 'monthly', 'yearly'
    
    # The date the recurrence should begin
    start_date = db.Column(db.Date, nullable=False)
    
    # The date the next transaction should be created
    next_due_date = db.Column(db.Date, nullable=False)
    
    # Foreign Keys to link to other models
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    
    # A recurring transaction is linked to a single category
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True) # Nullable for income
    
    # Define relationships to load related objects
    account = db.relationship('Account', backref='recurring_transactions')
    category = db.relationship('Category', backref='recurring_transactions')