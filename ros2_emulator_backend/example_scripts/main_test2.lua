-- DeltaARM Robot Test Script (main_test2.lua)
-- This script demonstrates DeltaAPI functions in the emulator

print("=== DeltaARM Robot Emulator Test Script ===")
print("")

-- Set up global points for robot movement
print("Setting up global points...")
SetGlobalPoint(1, "GL_P1", 200, 200, -100, 0, 0, 0, 0, 0, 0, 0, 0, {0,0,0,1,0,0,0,4})
SetGlobalPoint(2, "GL_P2", 300, 100, -100, 0, 0, 0, 0, 0, 0, 0, 0, {0,0,0,1,0,0,0,4})
SetGlobalPoint(3, "GL_P3", 200, 0, -100, 0, 0, 0, 0, 0, 0, 0, 0, {0,0,0,1,0,0,0,4})
print("Global points configured")
print("")

-- Set motion parameters
print("Configuring motion parameters...")
SpdJ(50)  -- Set joint speed to 50%
AccJ(20)  -- Set joint acceleration to 20%
DecJ(20)  -- Set joint deceleration to 20%
SpdL(500) -- Set linear speed to 500 mm/sec
AccL(1000) -- Set linear acceleration to 1000 mm/sec²
DecL(1000) -- Set linear deceleration to 1000 mm/sec²
Accur("STANDARD") -- Set accuracy to STANDARD
print("Motion parameters set")
print("")

-- Digital Output Test
print("Testing Digital Outputs...")
DO(1, "ON")
print("DO1 turned ON")
DELAY(0.5)
DO(1, "OFF")
print("DO1 turned OFF")
print("")

-- Digital Input Test (simulated)
print("Testing Digital Input read...")
di_status = DI(1)
print("DI1 status: " .. di_status)
print("")

-- Modbus Test
print("Testing Modbus operations...")
WriteModbus(0x1000, "W", 12345)
print("Written 12345 to Modbus address 0x1000")
value = ReadModbus(0x1000, "W")
print("Read value from 0x1000: " .. value)
print("")

-- Motion Test
print("Executing motion sequence...")
MovP(1)
print("Moved to Point 1")
DELAY(0.3)

MovL(2)
print("Linear move to Point 2")
DELAY(0.3)

MovP(3)
print("Moved to Point 3")
DELAY(0.3)

-- Return to start
MovL(1)
print("Returned to Point 1")
print("")

-- Multiple DO Test
print("Testing multiple outputs...")
DO(1, "ON")
DO(2, "ON")
DELAY(0.2)
DO(1, "OFF")
DO(2, "OFF")
print("Multiple outputs toggled")
print("")

-- Joint move test
print("Testing joint movement...")
MovJ(1, 45.0)
print("Joint 1 moved to 45 degrees")
DELAY(0.3)
MovJ(1, 0.0)
print("Joint 1 returned to 0 degrees")
print("")

print("=== Test Script Complete ===")
