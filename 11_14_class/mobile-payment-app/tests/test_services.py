from src.mobile_payment_app.services.gps import get_location
from src.mobile_payment_app.services.qr_scanner import generate_qr_code, scan_qr_code
from src.mobile_payment_app.services.barcode_scanner import generate_barcode, scan_barcode

def test_get_location():
    location = get_location()
    assert location is not None
    assert 'latitude' in location
    assert 'longitude' in location

def test_generate_qr_code():
    data = "Test Payment Data"
    qr_code = generate_qr_code(data)
    assert qr_code is not None
    assert isinstance(qr_code, bytes)

def test_scan_qr_code():
    qr_code_image = b"fake_qr_code_image_data"
    data = scan_qr_code(qr_code_image)
    assert data == "Test Payment Data"

def test_generate_barcode():
    data = "Test Barcode Data"
    barcode = generate_barcode(data)
    assert barcode is not None
    assert isinstance(barcode, bytes)

def test_scan_barcode():
    barcode_image = b"fake_barcode_image_data"
    data = scan_barcode(barcode_image)
    assert data == "Test Barcode Data"