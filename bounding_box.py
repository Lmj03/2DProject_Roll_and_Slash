from dataclasses import dataclass


@dataclass(frozen=True)
class BoundingBox:
    """An axis-aligned rectangle in Pico2d's bottom-left coordinates."""

    left: float
    bottom: float
    right: float
    top: float

    def overlaps(self, other):
        # Touching the edge alone does not count as a hit.
        return (self.left < other.right and other.left < self.right
                and self.bottom < other.top and other.bottom < self.top)

    def ellipse_overlaps(self, other):
        """Treat this box as the outer bounds of an ellipse for a second overlap check."""
        if not self.overlaps(other):
            return False
        rx, ry = (self.right - self.left) / 2, (self.top - self.bottom) / 2
        cx, cy = self.left + rx, self.bottom + ry
        x = min(max(cx, other.left), other.right)
        y = min(max(cy, other.bottom), other.top)
        return ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 < 1

    def contains(self, x, y):
        return self.left <= x <= self.right and self.bottom <= y <= self.top

    def expanded(self, padding):
        return BoundingBox(self.left - padding, self.bottom - padding,
                           self.right + padding, self.top + padding)
