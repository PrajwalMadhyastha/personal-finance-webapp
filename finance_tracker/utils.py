# finance_tracker/utils.py

from datetime import datetime, timezone
from flask_login import current_user
from .models import Tag
from . import db

def process_tags(transaction_object, tag_string):
    """
    Processes a comma-separated string of tags, associating them with a
    transaction object. Finds existing tags or creates new ones as needed.

    Args:
        transaction_object: The SQLAlchemy transaction model instance.
        tag_string: A string of tags, e.g., "work, travel, important".
    """
    # Clear existing tags to prevent duplicates, especially during edits
    transaction_object.tags.clear()
    
    if tag_string:
        tag_names = [name.strip().lower() for name in tag_string.split(',') if name.strip()]
        for tag_name in tag_names:
            # Check if a tag with this name already exists for the user
            tag = db.session.execute(
                db.select(Tag).filter(
                    db.func.lower(Tag.name) == tag_name,
                    Tag.user_id == current_user.id
                )
            ).scalar_one_or_none()

            # If the tag doesn't exist, create it
            if not tag:
                tag = Tag(name=tag_name, user_id=current_user.id)
                db.session.add(tag)
            
            # Add the tag to the transaction's relationship
            transaction_object.tags.append(tag)

def parse_date_range(request_args):
    """
    Parses start_date and end_date from request arguments, providing
    sensible defaults for the current month if they are not present.

    Args:
        request_args: The request.args object from Flask.

    Returns:
        A tuple containing (start_date_obj, end_date_obj, start_date_str, end_date_str).
    """
    now_utc = datetime.now(timezone.utc)
    # Default to the first day of the current month
    first_day_of_month = now_utc.replace(day=1).date()
    
    start_date_str = request_args.get('start_date', first_day_of_month.strftime('%Y-%m-%d'))
    end_date_str = request_args.get('end_date', now_utc.date().strftime('%Y-%m-%d'))

    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        # Fallback to defaults if date format is invalid
        start_date = first_day_of_month
        end_date = now_utc.date()
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')

    return start_date, end_date, start_date_str, end_date_str

def format_datetime(value):
    """
    A custom Jinja2 filter to format a datetime object into an
    ISO 8601 string, which is perfect for JavaScript to parse.
    """
    if value is None:
        return ""
    # Outputs a string like "2025-06-17T12:30:00Z"
    return value.isoformat()