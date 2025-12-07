#!/usr/bin/env python3
"""
Helper script to find the correct fcntl constants on z/OS
"""
import fcntl
import os
import sys

print("Checking fcntl module for z/OS file tagging constants...")
print()

# Check what's available in fcntl module
print("Available constants in fcntl module:")
for name in dir(fcntl):
    if name.startswith('F_'):
        value = getattr(fcntl, name)
        if isinstance(value, int):
            print(f"  {name} = {value}")

print()

# Try to find F_CONTROL_CVT which is documented for z/OS
try:
    F_CONTROL_CVT = getattr(fcntl, 'F_CONTROL_CVT', None)
    if F_CONTROL_CVT:
        print(f"Found F_CONTROL_CVT = {F_CONTROL_CVT}")
    else:
        print("F_CONTROL_CVT not found in fcntl module")
except:
    print("Could not access F_CONTROL_CVT")

print()

# According to IBM docs, F_CONTROL_CVT is used for conversion control
# Let's try some common values
print("Testing potential constant values...")
test_file = "/tmp/test_fcntl.txt"

# Create a test file
with open(test_file, 'w') as f:
    f.write("test\n")

try:
    fd = os.open(test_file, os.O_RDONLY)
    
    # Try different constant values
    for const_val in range(10, 20):
        try:
            import struct
            buffer = bytearray(20)
            result = fcntl.ioctl(fd, const_val, buffer)
            print(f"  Constant {const_val}: SUCCESS - returned {len(result) if isinstance(result, (bytes, bytearray)) else result}")
        except OSError as e:
            print(f"  Constant {const_val}: {e}")
    
    os.close(fd)
finally:
    if os.path.exists(test_file):
        os.unlink(test_file)

# Made with Bob
