# Use a specific version of Debian 11 (Bullseye) for consistency
FROM python:3.11-slim-bullseye

# Set the working directory in the container
WORKDIR /app

# --- Install System Dependencies & Microsoft ODBC Driver ---
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl gnupg apt-transport-https ca-certificates lsb-release \
    # Add the Microsoft GPG key
    && curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    # Add the Microsoft repository
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/11/prod bullseye main" > /etc/apt/sources.list.d/mssql-release.list \
    # Update package lists again to include the new repo
    && apt-get update \
    # Install the driver and tools, accepting the EULA
    && ACCEPT_EULA=Y apt-get install -y unixodbc-dev msodbcsql18 mssql-tools18 \
    # Clean up the apt cache to keep the image size small
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# --- THIS IS THE CRITICAL FIX ---
# Step 5: Add the SQL Server tools to the system's PATH environment variable
ENV PATH="/opt/mssql-tools18/bin:${PATH}"

# --- Verification Step ---
# Let's confirm the driver and tools are registered and findable during the build
RUN echo "--- Verifying installations ---" && \
    odbcinst -q -d && \
    which sqlcmd

# --- Python Dependencies & Application Code ---
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# --- Final Configuration ---
EXPOSE 5000
CMD ["python", "run.py"]

LABEL org.opencontainers.image.source="https://github.com/prajwalmadhyastha/personal-finance-webapp"