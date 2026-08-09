from gpiozero import OutputDevice


class SSR:
    """A class to control a Solid State Relay (SSR) using GPIO."""

    def __init__(self, pin: int):
        """Initialize the SSR with the specified GPIO pin."""
        self.relay = OutputDevice(pin)

    def on(self):
        """Turn the SSR on."""
        self.relay.on()

    def off(self):
        """Turn the SSR off."""
        self.relay.off()

    def is_on(self) -> bool:
        """Check if the SSR is currently on."""
        return self.relay.is_active