"""symbolic_robot: one engine for simulated, symbolic robots. A skill does not run for real; it returns an outcome drawn from
declared probabilities over a small symbolic world. Domains (factory, home, ...) plug in through `symbolic_robot.registry`."""
from .clock import SimClock  # noqa: F401
from .result import Result  # noqa: F401
from .rng import CallDraws, Rng  # noqa: F401

__version__ = "0.1.0"
