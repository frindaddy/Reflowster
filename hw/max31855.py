import adafruit_max31855
import board
import digitalio


class MAX31855:
    """A class to interface with the MAX31855 thermocouple amplifier."""
    
    def __init__(self):
        """Initialize the MAX31855 sensor."""
        self.spi = board.SPI()
        self.cs = digitalio.DigitalInOut(board.D5)
        self.sensor = adafruit_max31855.MAX31855(self.spi, self.cs)
        
    def read_temperature(self) -> float:
        """Read the temperature from the MAX31855 sensor."""
        return self.sensor.temperature
