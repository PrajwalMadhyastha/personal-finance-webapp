# finance_tracker/forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, SelectField, TextAreaField, SubmitField, RadioField, DateTimeField
# 1. Import ValidationError here
from wtforms.validators import DataRequired, Length, NumberRange, Optional, ValidationError
from wtforms_sqlalchemy.fields import QuerySelectField
from flask_login import current_user
from .models import Account, Category, db
from sqlalchemy import select
from datetime import datetime

def get_user_accounts():
    return db.session.execute(select(Account).filter_by(user_id=current_user.id).order_by(Account.name)).scalars()

def get_user_categories():
    return db.session.execute(select(Category).filter_by(user_id=current_user.id).order_by(Category.name)).scalars()

class TransactionForm(FlaskForm):
    transaction_type = RadioField(
        'Transaction Type', 
        choices=[('expense', 'Expense'), ('income', 'Income')],
        default='expense', # Set a default value
        validators=[DataRequired()]
    )
    description = StringField(
        'Description', 
        validators=[DataRequired(), Length(min=2, max=200)]
    )
    amount = DecimalField(
        'Amount (₹)', 
        places=2, 
        validators=[DataRequired(), NumberRange(min=0.01, message="Amount must be positive.")]
    )
    account = QuerySelectField(
        'Account',
        query_factory=get_user_accounts,
        get_label='name',
        allow_blank=False,
        validators=[DataRequired(message="You must select an account.")]
    )
    category = QuerySelectField(
        'Category',
        query_factory=get_user_categories,
        get_label='name',
        allow_blank=True,
        blank_text='-- Select a Category --',
        validators=[Optional()]
    )
    transaction_date = DateTimeField(
        'Date & Time', 
        format='%Y-%m-%dT%H:%M', 
        default=datetime.utcnow, 
        validators=[DataRequired()],
        render_kw={'class': 'flatpickr-datetime'} # ADD THIS
    )
    tags = StringField(
        'Tags (comma-separated)', 
        validators=[Optional(), Length(max=255)]
    )
    notes = TextAreaField(
        'Notes', 
        validators=[Optional(), Length(max=500)]
    )
    submit = SubmitField('Save Transaction')

    # Custom validator
    def validate_category(self, field):
        if self.transaction_type.data == 'expense' and not field.data:
            # 2. Use ValidationError instead of ValueError
            raise ValidationError('A category is required for expenses.')