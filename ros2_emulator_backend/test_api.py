"""
Simple test script to verify DeltaAPI implementation.

Run this script to test basic functionality of the emulator.
"""

import requests
import json

BASE_URL = "http://localhost:5000/api"


def test_digital_output():
    """Test Digital Output functionality."""
    print("Testing Digital Output...")
    response = requests.post(
        f"{BASE_URL}/do",
        json={"pin": 1, "status": "ON"}
    )
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    print("✓ Digital Output test passed\n")


def test_digital_input():
    """Test Digital Input functionality."""
    print("Testing Digital Input...")
    response = requests.post(
        f"{BASE_URL}/di",
        json={"pin": 1}
    )
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    print("✓ Digital Input test passed\n")


def test_modbus():
    """Test Modbus read/write functionality."""
    print("Testing Modbus operations...")
    
    # Write
    write_response = requests.post(
        f"{BASE_URL}/modbus/write",
        json={"address": 4096, "size": "W", "value": 12345}
    )
    print(f"Write Response: {write_response.json()}")
    assert write_response.status_code == 200
    
    # Read
    read_response = requests.post(
        f"{BASE_URL}/modbus/read",
        json={"address": 4096, "size": "W"}
    )
    print(f"Read Response: {read_response.json()}")
    assert read_response.status_code == 200
    assert read_response.json()['value'] == 12345
    print("✓ Modbus test passed\n")


def test_point_management():
    """Test point set/get functionality."""
    print("Testing Point Management...")
    
    # Set point
    set_response = requests.post(
        f"{BASE_URL}/point/set",
        json={
            "point_num": 1,
            "name": "GL_P1",
            "x": 200.0,
            "y": 200.0,
            "z": -100.0
        }
    )
    print(f"Set Point Response: {set_response.json()}")
    assert set_response.status_code == 200
    
    # Get point
    get_response = requests.get(f"{BASE_URL}/point/get/1")
    print(f"Get Point Response: {get_response.json()}")
    assert get_response.status_code == 200
    print("✓ Point Management test passed\n")


def test_script_execution():
    """Test Lua script execution."""
    print("Testing Lua Script Execution...")
    
    script = """
print("Hello from Lua!")
DO(1, "ON")
DELAY(0.1)
DO(1, "OFF")
WriteModbus(0x1000, "W", 999)
value = ReadModbus(0x1000, "W")
print("Modbus value: " .. value)
"""
    
    response = requests.post(
        f"{BASE_URL}/script/execute",
        json={"script": script}
    )
    result = response.json()
    print(f"Script Status: {result['status']}")
    print("Script Output:")
    for line in result['output']:
        print(f"  {line}")
    assert response.status_code == 200
    assert result['status'] == 'success'
    print("✓ Script Execution test passed\n")


def test_robot_state():
    """Test robot state retrieval."""
    print("Testing Robot State...")
    response = requests.get(f"{BASE_URL}/robot/position")
    print(f"Robot State: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200
    print("✓ Robot State test passed\n")


if __name__ == "__main__":
    print("=" * 60)
    print("DeltaARM Robot Emulator API Tests")
    print("=" * 60)
    print()
    
    try:
        test_digital_output()
        test_digital_input()
        test_modbus()
        test_point_management()
        test_script_execution()
        test_robot_state()
        
        print("=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to server.")
        print("Make sure the server is running on port 5000")
        print("Run: python run.py")
    except Exception as e:
        print(f"ERROR: Test failed - {e}")
