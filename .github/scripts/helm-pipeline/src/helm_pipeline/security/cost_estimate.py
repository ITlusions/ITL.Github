"""Estimate what a security scan step costs on a GitHub-hosted runner."""

import math

# AI generated code: GitHub Copilot Claude Haiku 5.5
# List price in USD per minute for a Linux 2-core standard runner in a private repository.
DEFAULT_PRICE_PER_MINUTE = 0.008


class CostEstimate:
    """Convert the duration of a scan step into billed runner minutes and an estimated cost."""

    def __init__(self, price_per_minute=DEFAULT_PRICE_PER_MINUTE):
        """Store the runner price per minute.

        Args:
            price_per_minute: Price in USD for one billed runner minute.
        """
        self.price_per_minute = price_per_minute

    def billed_minutes(self, seconds):
        """Return the billed minutes for a duration, rounded up to a whole minute with a minimum of one.

        Args:
            seconds: Duration of the scan step in seconds.

        Returns:
            The number of billed minutes.
        """
        return max(1, math.ceil(seconds / 60))

    def cost(self, minutes):
        """Return the estimated cost in USD for a number of billed minutes."""
        return minutes * self.price_per_minute
