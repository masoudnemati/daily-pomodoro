import requests
import logging
from datetime import datetime

# Set up a logger just for sun events
logger = logging.getLogger("sun")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s [%(name)s] %(message)s"))
logger.addHandler(handler)


class Sun:
    def __init__(self, city: str, country: str):
        self.city = city
        self.country = country
        self.sunrise = None
        self.sunset = None
        self.solar_noon = None
        self.update()

    def update(self):
        try:
            # 1. Geocode the city
            geo = requests.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={
                    "name": self.city,
                    "count": 1,
                    "language": "en",
                    "format": "json",
                },
                timeout=10,
            ).json()
            result = geo["results"][0]
            latitude = result["latitude"]
            longitude = result["longitude"]

            # 2. Fetch today's sunrise & sunset
            weather = requests.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": latitude,
                    "longitude": longitude,
                    "daily": "sunrise,sunset",
                    "timezone": "auto",
                },
                timeout=10,
            ).json()

            self.sunrise = datetime.fromisoformat(
                weather["daily"]["sunrise"][0]
            )
            self.sunset = datetime.fromisoformat(
                weather["daily"]["sunset"][0]
            )

            # 3. Calculate solar noon (midpoint between sunrise and sunset)
            self.solar_noon = self.sunrise + (self.sunset - self.sunrise) / 2

            # 4. Log everything
            logger.info(
                "Sun times for %s, %s:", self.city, self.country
            )
            logger.info("  ☀️ Sunrise:     %s", self.sunrise.strftime("%H:%M:%S"))
            logger.info("  ☀️ Solar noon:  %s", self.solar_noon.strftime("%H:%M:%S"))
            logger.info("  ☀️ Sunset:      %s", self.sunset.strftime("%H:%M:%S"))

        except Exception as e:
            logger.error("Failed to fetch sun data: %s", e)