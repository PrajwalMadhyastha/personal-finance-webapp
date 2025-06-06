#!/bin/bash

# --- Scaffolding script to create boilerplate for a new feature ---
# This script creates a new routes file and a corresponding template
# for a new feature in the Flask application.

# 1. Check if exactly one argument (the feature name) was provided.
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <feature_name>"
    echo "Example: ./new_feature.sh reporting"
    echo "Note: Feature name should be lowercase, use underscores for spaces (e.g., 'user_profile')."
    exit 1
fi

# 2. Assign argument and validate it.
FEATURE_NAME="$1"
if ! [[ "$FEATURE_NAME" =~ ^[a-z_]+$ ]]; then
    echo "Error: Feature name must contain only lowercase letters and underscores."
    exit 1
fi

# 3. Define the paths for the new files.
# The script assumes it's being run from the project root directory.
ROUTES_FILE="finance_tracker/${FEATURE_NAME}_routes.py"
TEMPLATE_FILE="finance_tracker/templates/${FEATURE_NAME}.html"

# 4. Check if files already exist to prevent overwriting.
if [ -f "$ROUTES_FILE" ] || [ -f "$TEMPLATE_FILE" ]; then
    echo "Error: Files for feature '$FEATURE_NAME' already exist."
    echo "  - $ROUTES_FILE"
    echo "  - $TEMPLATE_FILE"
    exit 1
fi

echo "Creating new feature: $FEATURE_NAME"
echo "  -> Route file: $ROUTES_FILE"
echo "  -> Template file: $TEMPLATE_FILE"

# 5. Create the boilerplate for the routes file.
cat << EOF > "$ROUTES_FILE"
from flask import Blueprint, render_template

# Create a Blueprint for the '$FEATURE_NAME' feature.
${FEATURE_NAME}_bp = Blueprint(
    '${FEATURE_NAME}', 
    __name__,
    template_folder='templates'
)

@${FEATURE_NAME}_bp.route('/${FEATURE_NAME}')
def index():
    """Render the main page for the ${FEATURE_NAME} feature."""
    return render_template('${FEATURE_NAME}.html')

# Add more routes for this feature here...
EOF

# 6. Create the boilerplate for the template file.
# Create a title-cased version of the name for the HTML title.
first_char=$(echo "$FEATURE_NAME" | cut -c1 | tr 'a-z' 'A-Z')
rest_of_name=$(echo "$FEATURE_NAME" | cut -c2-)
FEATURE_NAME_TITLE_CASE="${first_char}${rest_of_name}"

cat << EOF > "$TEMPLATE_FILE"
{% extends "base.html" %}

{% block title %}${FEATURE_NAME_TITLE_CASE} Page{% endblock %}

{% block content %}
    <h1>Welcome to the ${FEATURE_NAME_TITLE_CASE} Feature!</h1>
    <p>Content for the '${FEATURE_NAME}' feature will go here.</p>
{% endblock %}
EOF

# 7. Print success message and next steps.
echo ""
echo "Successfully created boilerplate files for feature: $FEATURE_NAME"
echo ""
echo "IMPORTANT NEXT STEP:"
echo "You must now register the new blueprint in your application factory."
echo "Open 'finance_tracker/__init__.py' and add the following lines inside the create_app() function:"
echo ""
echo "    # --- Inside create_app() in __init__.py ---"
echo "    from .${FEATURE_NAME}_routes import ${FEATURE_NAME}_bp"
echo "    app.register_blueprint(${FEATURE_NAME}_bp)"
echo ""