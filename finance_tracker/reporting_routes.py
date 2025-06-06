from flask import Blueprint, render_template

# Create a Blueprint for the 'reporting' feature.
reporting_bp = Blueprint(
    'reporting', 
    __name__,
    template_folder='templates'
)

@reporting_bp.route('/reporting')
def index():
    """Render the main page for the reporting feature."""
    return render_template('reporting.html')

# Add more routes for this feature here...
