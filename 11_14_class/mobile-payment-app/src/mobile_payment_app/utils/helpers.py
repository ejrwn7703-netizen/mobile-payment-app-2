def generate_response(data):
    return {
        "status": "success",
        "data": data
    }

def handle_error(message):
    return {
        "status": "error",
        "message": message
    }

def validate_input(data, required_fields):
    for field in required_fields:
        if field not in data:
            return False, f"Missing required field: {field}"
    return True, None

def format_currency(amount):
    return "${:,.2f}".format(amount)