# Personal Finance Web Application

<p>This is a comprehensive personal finance web application built as a long-term learning project. It provides users with tools to track income, expenses, budgets, and investments. The primary focus of the project is not just the application itself, but the modern cloud and DevOps technologies used to build, test, deploy, and manage it.</p>

<p>The application is fully containerized with Docker, deployed to Microsoft Azure using Infrastructure as Code (Terraform), and features a complete CI/CD pipeline with GitHub Actions for automated linting, testing, and deployment.</p>

---

## ✨ Features

* **Secure User Authentication:** Full registration, login, and password management using Flask-Login and Bcrypt for password hashing.
* **Transaction Management:** Full CRUD (Create, Read, Update, Delete) capabilities for income and expense transactions.
* **Account Tracking:** Users can create multiple financial accounts (e.g., Checking, Savings, Credit Card) and track balances in real-time.
* **Budgeting System:** Set monthly spending budgets for specific categories and visually track progress on the dashboard.
* **Investment Portfolio:** Record buy/sell transactions for assets like stocks and view a high-level summary of current holdings.
* **Tagging System:** Apply multiple, custom tags to transactions for powerful filtering and organization.
* **Recurring Transactions:** Schedule regular income or expenses (e.g., salary, subscriptions) to be automatically logged via a secure, scheduled job.
* **Interactive Reporting:** Dynamic dashboard with date-range filters, pie and line charts, and detailed monthly/yearly summary reports.
* **Secure File Uploads:** Users can upload a profile picture, which is stored securely in Azure Blob Storage.
* **Bulk Import:** Upload transactions from a standard CSV file with smart data handling.
* **Secure API:** A dedicated API for programmatic access, protected by user-generated API keys.
* **Automated Auditing & CI/CD:**
    * Code is automatically linted with `flake8` and `shellcheck`.
    * A full test suite using `pytest` is run on every deployment.
    * Code coverage reports are generated and uploaded as artifacts.
    * A multi-job GitHub Actions pipeline handles testing, building, database migrations, and deployment.

---

## 🛠️ Technology Stack

* **Backend:** Python, Flask, Flask-WTF, SQLAlchemy
* **Database (Production):** Azure SQL Database (Serverless)
* **Database (Local):** Microsoft SQL Server (Docker Container)
* **File Storage:** Azure Blob Storage
* **Cloud Platform:** Microsoft Azure
* **Hosting:** Azure Container Apps
* **Container Registry:** GitHub Container Registry (GHCR)
* **Infrastructure as Code (IaC):** Terraform
* **Containerization:** Docker, Docker Compose
* **CI/CD:** GitHub Actions
* **Testing:** Pytest, pytest-cov
* **Linting:** flake8, shellcheck

---

## 🚀 Local Development Setup

To run this project on your local machine, you will need `git` and `docker` (with Docker Compose) installed.

### 1. Clone the Repository
```bash
git clone [https://github.com/YourUsername/personal-finance-webapp.git](https://github.com/YourUsername/personal-finance-webapp.git)
cd personal-finance-webapp
```
### 2. Set Up Environment Variables
The application requires a `.env` file for its configuration. A helper script is provided to create this from a template.

```bash
# This will create a .env file from the .env.example template
./scripts/setup_env.sh
```
Now, **open the new `.env` file** in your code editor. You must fill in the following values:

* `SECRET_KEY` and `TASK_SECRET_KEY`: Generate two long, random strings for these. You can use below command in your terminal to generate one.
```bash
openssl rand -hex 32
```

* `DB_SA_PASSWORD` and `DB_ADMIN_PASSWORD`: Set these to the same complex password for the local database (e.g., `Your.Strong.Password123!`).

### 3. Start the Local Environment
The project uses a `manage.sh` script to orchestrate Docker Compose.

#### a) Start the Database (One-time setup)

First, start the standalone database container. This will be slow the first time as it downloads the SQL Server image.

```bash
./scripts/manage.sh start-db
```

*Wait a minute or two for the database to become healthy. You can check its status with `docker ps`.

#### b) Apply Database Migrations

Once the database is running, you need to create all the application tables.

```bash
./scripts/manage.sh db upgrade
```
#### c) Start the Application

Finally, start the Flask web application container.

```bash
./scripts/manage.sh start-app
```
Your local development environment is now fully running! You can access the application in your web browser at `http://localhost:5000`.

## ☁️ Cloud Deployment & CI/CD Setup
To enable the automated deployment pipeline for your own fork of this repository, you must configure the following secrets in your GitHub repo.

Navigate to **Settings > Secrets and variables > Actions** and create the following **Repository secrets**:

* `AZURE_CREDENTIALS`: The JSON output from creating an Azure Service Principal with contributor rights to your resource group.

```bash
az ad sp create-for-rbac --name "pfa-github-actions" --role contributor --scopes /subscriptions/YOUR_SUBSCRIPTION_ID/resourceGroups/YOUR_RESOURCE_GROUP_NAME --sdk-auth
```

* `DB_ADMIN_LOGIN`: The administrator username you chose for your Azure SQL Server.

* `DB_ADMIN_PASSWORD`: The administrator password for your Azure SQL Server.

* `FLASK_SECRET_KEY`: A long, random string for your live application's secret key. You can use below command in your terminal to generate one.

```bash
openssl rand -hex 32
```

* `RECURRING_JOB_SECRET`: A separate, long, random string used to authorize the scheduled job. You can use below command in your terminal to generate one.

```bash
openssl rand -hex 32
```

* `GHCR_PAT`: A GitHub Personal Access Token (classic) with `write:packages` scope. This is needed for Terraform to configure access to the GitHub Container Registry.