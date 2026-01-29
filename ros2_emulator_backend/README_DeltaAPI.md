# DeltaARM Robot Emulator - DeltaAPI Implementation

This ROS2 emulator backend provides a complete implementation of the DeltaAPI specification for the DeltaARM robot, including a Lua-like scripting interface.

## Features

### 1. **DeltaAPI Functions**
All major DeltaAPI functions are implemented:

#### Digital I/O
- `DI(pin, [length])` - Read Digital Input
- `DO(pin, status, [delay])` - Set Digital Output
- `ExtDI(address, pin)` - Read External Digital Input
- `ExtDO(address, pin, status, [delay])` - Set External Digital Output

#### Motion Control
- `MovP(point)` - Move to point (joint motion)
- `MovL(point)` - Move to point (linear motion)
- `MovJ(joint, degree)` - Move single joint
- `SetGlobalPoint(...)` - Define global points
- `ReadPoint(point, item)` - Read point information

#### Speed & Acceleration
- `SpdJ(speed)` - Set joint speed (%)
- `AccJ(acceleration)` - Set joint acceleration (%)
- `DecJ(deceleration)` - Set joint deceleration (%)
- `SpdL(speed)` - Set linear speed (mm/sec)
- `AccL(acceleration)` - Set linear acceleration (mm/sec²)
- `DecL(deceleration)` - Set linear deceleration (mm/sec²)
- `Accur(mode)` - Set in-place accuracy

#### Timing
- `WAIT(...)` - Wait for condition or timeout
- `DELAY(time)` - Delay execution

#### Modbus
- `ReadModbus(address, size)` - Read Modbus register
- `WriteModbus(address, size, value)` - Write Modbus register

### 2. **Lua Scripting Support**
- Full Lua interpreter integration using `lupa`
- Execute Lua scripts with DeltaAPI functions
- Upload and run `.lua` files
- Real-time execution logging

### 3. **REST API Endpoints**

All endpoints are available at `/api` prefix:

#### Digital I/O
- `POST /api/di` - Read Digital Input
- `POST /api/do` - Set Digital Output
- `GET /api/do` - Get all DO states

#### Modbus
- `POST /api/modbus/read` - Read Modbus register
- `POST /api/modbus/write` - Write Modbus register

#### Point Management
- `POST /api/point/set` - Set global point
- `GET /api/point/get/<point_num>` - Get point data

#### Robot State
- `GET /api/robot/position` - Get current position and state

#### Script Execution
- `POST /api/script/execute` - Execute Lua script code
- `POST /api/script/upload` - Upload and execute .lua file

## API Usage Examples

### Digital I/O

**Read Digital Input:**
```bash
curl -X POST http://localhost:3001/api/di \
  -H "Content-Type: application/json" \
  -d '{"pin": 1}'
```

**Set Digital Output:**
```bash
curl -X POST http://localhost:3001/api/do \
  -H "Content-Type: application/json" \
  -d '{"pin": 1, "status": "ON"}'
```

### Modbus Operations

**Read Modbus Register:**
```bash
curl -X POST http://localhost:3001/api/modbus/read \
  -H "Content-Type: application/json" \
  -d '{"address": 4096, "size": "W"}'
```

**Write Modbus Register:**
```bash
curl -X POST http://localhost:3001/api/modbus/write \
  -H "Content-Type: application/json" \
  -d '{"address": 4096, "size": "W", "value": 12345}'
```

### Point Management

**Set Global Point:**
```bash
curl -X POST http://localhost:3001/api/point/set \
  -H "Content-Type: application/json" \
  -d '{
    "point_num": 1,
    "name": "GL_P1",
    "x": 200.0,
    "y": 200.0,
    "z": -100.0
  }'
```

### Script Execution

**Execute Lua Script:**
```bash
curl -X POST http://localhost:3001/api/script/execute \
  -H "Content-Type: application/json" \
  -d '{
    "script": "DO(1, \"ON\")\nDELAY(0.5)\nDO(1, \"OFF\")\nprint(\"Script complete\")"
  }'
```

**Upload Lua File:**
```bash
curl -X POST http://localhost:3001/api/script/upload \
  -F "file=@example_scripts/main_test2.lua"
```

## Lua Script Example

See `example_scripts/main_test2.lua` for a comprehensive example:

```lua
-- Set up points
SetGlobalPoint(1, "GL_P1", 200, 200, -100, 0, 0, 0, 0, 0, 0, 0, 0, {0,0,0,1,0,0,0,4})

-- Configure motion
SpdJ(50)
AccJ(20)

-- Digital output
DO(1, "ON")
DELAY(0.5)
DO(1, "OFF")

-- Motion
MovP(1)
DELAY(0.3)

-- Modbus
WriteModbus(0x1000, "W", 12345)
value = ReadModbus(0x1000, "W")
print("Read value: " .. value)
```

## Architecture

### Components

1. **emulator_state.py**
   - Manages robot state (DI, DO, Modbus, position)
   - Thread-safe singleton pattern
   - Stores global points and motion settings

2. **lua_interpreter.py**
   - Lua runtime with DeltaAPI bindings
   - Executes scripts with full API access
   - Logs execution output

3. **routes/delta_api.py**
   - REST API endpoints
   - Flask-SMOREST with OpenAPI documentation
   - Request/response validation

### State Management

The emulator maintains:
- **Digital Inputs (DI)**: 24 pins (1-24)
- **Digital Outputs (DO)**: 12 pins (1-12)
- **Modbus Registers**: Addresses 0x1000-0x1FFF, 0x3000-0x3FFF
- **Robot Position**: X, Y, Z, RX, RY, RZ
- **Joint Angles**: 6 joints
- **Global Points**: 1-1000 points storage
- **Motion Settings**: Speed, acceleration, deceleration, accuracy

## Running the Emulator

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the server:**
   ```bash
   python run.py
   ```

3. **Access API documentation:**
   - Swagger UI: http://localhost:5000/docs
   - OpenAPI spec: http://localhost:5000/docs/openapi.json

## Testing

### Test with curl:
```bash
# Set a point
curl -X POST http://localhost:3001/api/point/set \
  -H "Content-Type: application/json" \
  -d '{"point_num": 1, "name": "GL_P1", "x": 200, "y": 200, "z": -100}'

# Execute script
curl -X POST http://localhost:3001/api/script/execute \
  -H "Content-Type: application/json" \
  -d '{"script": "MovP(1)\nprint(\"Moved to point 1\")"}'

# Check robot state
curl http://localhost:3001/api/robot/position
```

### Run example script:
```bash
curl -X POST http://localhost:3001/api/script/upload \
  -F "file=@example_scripts/main_test2.lua"
```

## DeltaAPI Specification

The implementation follows the official DeltaAPI specification (see `attachments/20260129_035350_DeltaAPI.txt`). All documented functions are available in the Lua scripting environment.

## Notes

- The emulator simulates robot behavior without actual hardware
- Motion commands update internal position state instantly (no timing simulation)
- All I/O states persist in memory during the session
- Thread-safe for concurrent requests
- Lua scripts execute synchronously (blocking)

## Future Enhancements

Potential additions:
- Socket communication (SocketClass, SocketServer)
- Multi-tasking support (AuxTasks, AuxTasksAdd)
- Motion timing simulation
- ROS2 topic publishing for state changes
- WebSocket support for real-time updates
