# Property Rental Management System

A comprehensive web-based property rental management system built with Python Flask and MySQL.

## Features

- Property Management
- Tenant Management
- Lease Management
- Payment Tracking
- User Authentication
- Role-based Access Control

## Prerequisites

- Python 3.8 or higher
- MySQL Server
- pip (Python package manager)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd property_rental_system
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

4. Set up the MySQL database:
- Create a new MySQL database
- Run the SQL commands in `database/schema.sql` to create the tables

5. Configure the database connection:
- Open `app.py` and update the database connection string with your MySQL credentials:
```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://username:password@localhost/database_name'
```

## Running the Application

1. Start the Flask development server:
```bash
python app.py
```

2. Open your web browser and navigate to:
```
http://localhost:5000
```

## Default Admin Account

- Username: admin
- Password: admin123

## Project Structure

```
property_rental_system/
├── app.py              # Main application file
├── requirements.txt    # Python dependencies
├── database/
│   └── schema.sql     # Database schema
├── static/            # Static files (CSS, JS, images)
└── templates/         # HTML templates
    ├── base.html      # Base template
    ├── login.html     # Login page
    ├── dashboard.html # Dashboard
    ├── properties.html # Properties management
    ├── tenants.html   # Tenants management
    ├── leases.html    # Leases management
    └── payments.html  # Payments management
```

## Database Schema

The system uses the following tables:

1. Properties
   - Property details (address, type, bedrooms, etc.)
   - Rental status and pricing

2. Tenants
   - Tenant information
   - Contact details
   - Employment status

3. Leases
   - Rental agreements
   - Property and tenant relationships
   - Lease terms and conditions

4. Payments
   - Rent payments
   - Security deposits
   - Maintenance payments

## Contributing

1. Fork the repository
2. Create a new branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 