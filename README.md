# Smart Inventory & Orders Tracker

CS340 – Introduction to Database Systems | Team Project

## Team Members
- Mahmood
- Abdullah AlQahtani
- Suliman
- Abdullah Altorifi

## Stack
- **Backend:** Python Flask
- **Database:** Supabase PostgreSQL (psycopg2)
- **Frontend:** HTML, Bootstrap 5, Jinja2

## Setup Instructions

### 1. Clone / download the project

### 2. Create a virtual environment
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
```bash
copy .env.example .env      # Windows
cp .env.example .env        # Mac/Linux
```
Edit `.env` and fill in your Supabase connection string and a secret key.

### 5. Run the app
```bash
python app.py
```
Visit: http://127.0.0.1:5000

## Features
- Dashboard with live stats (total products, customers, orders, revenue)
- Full CRUD for Products, Customers, Orders, Users
- Order creation with multiple items and automatic total calculation
- Query Reports page with 40 named SQL queries (organized by team member)
- Parameterized filter queries (by category, by customer)

## Database Schema
Tables: `Users`, `Admin`, `Product`, `Customer`, `Orders`, `OrderItem`

See schema in project report for full column definitions.
