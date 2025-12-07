#!/usr/bin/env python3
"""
Test what constant 18 does with file tagging
"""
import fcntl
import os
import struct
import subprocess

test_file = "/tmp/test_tag_819.txt"

# Create a test file and tag it as ISO8859-1
with open(test_file, 'w', encoding='iso8859-1') as f:
    f.write("test file\n")

# Tag it as ISO8859-1 using chtag
subprocess.run(['chtag', '-tc', 'ISO8859-1', test_file], check=True)

# Verify with ls -T
result = subprocess.run(['ls', '-T', test_file], capture_output=True, text=True)
print("ls -T output:")
print(result.stdout)
print()

# Now try constant 18 with different buffer sizes and formats
print("Testing constant 18 with different buffer configurations:")
print()

fd = os.open(test_file, os.O_RDONLY)

# Test 1: 20-byte buffer (attrib_t structure)
print("Test 1: 20-byte buffer (attrib_t: iihh2i)")
try:
    buffer = bytearray(20)
    result = fcntl.ioctl(fd, 18, buffer)
    print(f"  Success! Result type: {type(result)}")
    print(f"  Buffer hex: {buffer.hex()}")
    
    # Try to unpack as attrib_t
    filetagchg, rsvd1, txtflag, ccsid, rsvd2_1, rsvd2_2 = struct.unpack('iihh2i', buffer)
    print(f"  Unpacked as attrib_t:")
    print(f"    filetagchg={filetagchg}, rsvd1={rsvd1}")
    print(f"    txtflag={txtflag}, ccsid={ccsid}")
    print(f"    rsvd2=({rsvd2_1}, {rsvd2_2})")
except Exception as e:
    print(f"  Error: {e}")

print()

# Test 2: Try different unpack formats
print("Test 2: Try unpacking as different formats")
buffer = bytearray(20)
fcntl.ioctl(fd, 18, buffer)

formats = [
    ('20B', '20 bytes'),
    ('5i', '5 ints'),
    ('10h', '10 shorts'),
    ('iihh2i', 'attrib_t'),
    ('2i4h2i', 'alt format 1'),
    ('4h3i', 'alt format 2'),
]

for fmt, desc in formats:
    try:
        values = struct.unpack(fmt, buffer)
        print(f"  {desc} ({fmt}): {values}")
    except:
        print(f"  {desc} ({fmt}): unpack failed")

print()

# Test 3: Try with a file tagged as IBM-1047
print("Test 3: Testing with IBM-1047 tagged file")
test_file_1047 = "/tmp/test_tag_1047.txt"
with open(test_file_1047, 'w', encoding='ibm1047') as f:
    f.write("ebcdic test\n")
subprocess.run(['chtag', '-tc', 'IBM-1047', test_file_1047], check=True)

fd2 = os.open(test_file_1047, os.O_RDONLY)
buffer2 = bytearray(20)
fcntl.ioctl(fd2, 18, buffer2)
print(f"  Buffer hex: {buffer2.hex()}")

filetagchg, rsvd1, txtflag, ccsid, rsvd2_1, rsvd2_2 = struct.unpack('iihh2i', buffer2)
print(f"  txtflag={txtflag}, ccsid={ccsid}")

os.close(fd2)
os.unlink(test_file_1047)

print()

# Test 4: Try with untagged file
print("Test 4: Testing with untagged file")
test_file_untagged = "/tmp/test_untagged.txt"
with open(test_file_untagged, 'wb') as f:
    f.write(b"untagged\n")
subprocess.run(['chtag', '-r', test_file_untagged], check=True)

fd3 = os.open(test_file_untagged, os.O_RDONLY)
buffer3 = bytearray(20)
fcntl.ioctl(fd3, 18, buffer3)
print(f"  Buffer hex: {buffer3.hex()}")

filetagchg, rsvd1, txtflag, ccsid, rsvd2_1, rsvd2_2 = struct.unpack('iihh2i', buffer3)
print(f"  txtflag={txtflag}, ccsid={ccsid}")

os.close(fd3)
os.unlink(test_file_untagged)

os.close(fd)
os.unlink(test_file)

print()
print("Summary: Constant 18 appears to be the correct constant for getting file tags!")

# Made with Bob
