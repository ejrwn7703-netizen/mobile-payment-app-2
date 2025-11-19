from geopy.geocoders import Nominatim

class GPSService:
    def __init__(self):
        self.geolocator = Nominatim(user_agent="mobile_payment_app")

    def get_location(self):
        location = self.geolocator.geocode("Your location query here")
        if location:
            return {
                "latitude": location.latitude,
                "longitude": location.longitude,
                "address": location.address
            }
        return None

    def get_coordinates(self, address):
        location = self.geolocator.geocode(address)
        if location:
            return {
                "latitude": location.latitude,
                "longitude": location.longitude
            }
        return None