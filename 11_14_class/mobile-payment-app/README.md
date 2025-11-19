# Mobile Payment App

## Overview
The Mobile Payment App is an automated payment system that integrates GPS functionality and QR/barcode payment processing. This application allows users to make payments seamlessly using their mobile devices.

## Features
- **GPS Integration**: Access user location for purchase verification.
- **QR Code Payment**: Generate and scan QR codes for quick transactions.
- **Barcode Payment**: Generate and scan barcodes for payment processing.
- **User-Friendly Interface**: Simple and intuitive web interface for users.

## Project Structure
```
mobile-payment-app
├── src
│   └── mobile_payment_app
│       ├── __init__.py
│       ├── app.py
│       ├── config.py
│       ├── routes
│       │   ├── __init__.py
│       │   ├── api.py
│       │   └── payments.py
│       ├── services
│       │   ├── gps.py
│       │   ├── qr_scanner.py
│       │   └── barcode_scanner.py
│       ├── models
│       │   ├── __init__.py
│       │   └── transaction.py
│       ├── templates
│       │   └── index.html
│       ├── static
│       │   ├── css
│       │   │   └── styles.css
│       │   └── js
│       │       └── main.js
│       └── utils
│           └── helpers.py
├── tests
│   ├── test_routes.py
│   └── test_services.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

## Installation
1. Clone the repository:
   ```
   git clone <repository-url>
   ```
2. Navigate to the project directory:
   ```
   cd mobile-payment-app
   ```
3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage
1. Run the application:
   ```
   python src/mobile_payment_app/app.py
   ```
2. Access the application in your web browser at `http://127.0.0.1:8000`.

## Testing
To run the tests, use:
```
pytest tests/
```

## License
This project is licensed under the MIT License. See the LICENSE file for details.