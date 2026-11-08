"""Exact small zero-sum game certificates."""
from .core import solve,audit,perturbation
from .demo import demo
from .intervals import interval_audit,interval_demo
__version__='0.2.0'
__all__=['solve','audit','perturbation','demo','interval_audit','interval_demo']
