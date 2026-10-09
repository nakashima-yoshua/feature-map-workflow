import os
import sys

sys.path.insert(0, os.getcwd())
from app import value

assert value() == 2, "INV-VALUE: expected 2"
print("INV-VALUE: passed")
