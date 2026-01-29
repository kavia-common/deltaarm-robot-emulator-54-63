# DeltaARM Robot Emulator - Quick Start Guide

## Overview

This Flask-based emulator provides a complete implementation of the DeltaAPI specification with Lua scripting support for simulating DeltaARM robot operations without hardware.

## Installation

```bash
cd ros2_emulator_backend
pip install -r requirements.txt
```

## Starting the Server

```bash
python run.py
```

The server will start on `http://localhost:5000`

## Access Documentation

- **Swagger UI**: http://localhost:5000/docs
- **OpenAPI Spec**: http://localhost:5000/docs/openapi.json

## Quick Examples

### 1. Control Digital Output

```bash
curl -X POST http://localhost:5000/api/do \
  -H "Content-Type: application/json" \
  -d '{"pin": 1, "status": "ON"}'
```

### 2. Read Digital Input

```bash
curl -X POST http://localhost:5000/api/di \
  -H "Content-Type: application/json" \
  -d '{"pin": 1}'
```

### 3. Write/Read Modbus Register

```bash
# Write
curl -X POST http://localhost:5000/api/modbus/write \
  -H "Content-Type: application/json" \
  -d '{"address": 4096, "size": "W", "value": 12345}'

# Read
curl -X POST http://localhost:5000/api/modbus/read \
  -H "Content-Type: application/json" \
  -d '{"address": 4096, "size": "W"}'
```

### 4. Execute Lua Script

```bash
curl -X POST http://localhost:5000/api/script/execute \
  -H "Content-Type: application/json" \
  -d '{
    "script": "DO(1, \"ON\")\nDELAY(0.5)\nDO(1, \"OFF\")\nprint(\"Complete\")"
  }'
```

### 5. Upload and Run Lua Script File

```bash
curl -X POST http://localhost:5000/api/script/upload \
  -F "file=@example_scripts/main_test2.lua"
```

### 6. Set and Use Global Points

```bash
# Set a point
curl -X POST http://localhost:5000/api/point/set \
  -H "Content-Type: application/json" \
  -d '{
    "point_num": 1,
    "name": "GL_P1",
    "x": 200.0,
    "y": 200.0,
    "z": -100.0
  }'

# Use in Lua script
curl -X POST http://localhost:5000/api/script/execute \
  -H "Content-Type: application/json" \
  -d '{"script": "MovP(1)\nprint(\"Moved to point 1\")"}'
```

### 7. Check Robot State

```bash
curl http://localhost:5000/api/robot/position
```

## Running Tests

```bash
# Make sure server is running first
python test_api.py
```

## Example Lua Script

The `example_scripts/main_test2.lua` demonstrates:
- Setting up global points
- Configuring motion parameters
- Digital I/O operations
- Modbus read/write
- Motion commands (MovP, MovL, MovJ)
- Delays and timing

Run it with:
```bash
curl -X POST http://localhost:5000/api/script/upload \
  -F "file=@example_scripts/main_test2.lua"
```

## Available DeltaAPI Functions in Lua

### Digital I/O
- `DI(pin)` - Read digital input
- `DO(pin, status)` - Set digital output
- `ExtDI(address, pin)` - Read external DI
- `ExtDO(address, pin, status)` - Set external DO

### Motion
- `MovP(point)` - Joint motion to point
- `MovL(point)` - Linear motion to point
- `MovJ(joint, degree)` - Move single joint
- `SetGlobalPoint(num, name, x, y, z, ...)` - Define point
- `ReadPoint(point, item)` - Read point data

### Speed & Acceleration
- `SpdJ(speed)` - Joint speed (%)
- `AccJ(accel)` - Joint acceleration (%)
- `DecJ(decel)` - Joint deceleration (%)
- `SpdL(speed)` - Linear speed (mm/sec)
- `AccL(accel)` - Linear acceleration (mm/sec²)
- `DecL(decel)` - Linear deceleration (mm/sec²)
- `Accur(mode)` - Set accuracy (HIGH/STANDARD/MEDIUM/ROUGH/MAXROUGH)

### Timing
- `WAIT(io_type, pin, status, [timeout])` - Wait for condition
- `DELAY(seconds)` - Delay execution

### Modbus
- `ReadModbus(address, size)` - Read register (size: "W" or "DW")
- `WriteModbus(address, size, value)` - Write register

### Utility
- `print(...)` - Print to output log

## State Persistence

The emulator maintains state in memory:
- 24 Digital Input pins (1-24)
- 12 Digital Output pins (1-12)
- Modbus registers (0x1000-0x1FFF, 0x3000-0x3FFF)
- 1000 Global points (1-1000)
- Current robot position and joint angles
- Motion parameter settings

State persists for the duration of the server session.

## Deployment

For production deployment, use a WSGI server like Gunicorn:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:3001 run:app
```

## Troubleshooting

### Server won't start
- Check if port 5000 is already in use
- Verify all dependencies are installed: `pip install -r requirements.txt`

### Lua script errors
- Check script syntax
- Ensure all required points are defined before use
- Review script output in the response for error messages

### API returns 404
- Verify server is running
- Check endpoint path is correct (prefix with `/api`)
- Review OpenAPI spec at `/docs/openapi.json`

## Next Steps

1. Review the full API documentation at `/docs`
2. Examine `example_scripts/main_test2.lua` for script examples
3. Read `README_DeltaAPI.md` for detailed implementation notes
4. Check the DeltaAPI specification in `attachments/20260129_035350_DeltaAPI.txt`

## Support

For issues or questions, refer to:
- DeltaAPI specification document
- OpenAPI documentation at `/docs`
- Example scripts in `example_scripts/`
