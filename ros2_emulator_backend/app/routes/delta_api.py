"""
REST API Routes for DeltaAPI Functions

Exposes all DeltaAPI functions as REST endpoints at the root path.
"""

from flask import request
from flask_smorest import Blueprint
from flask.views import MethodView
from marshmallow import Schema, fields
from ..emulator_state import emulator_state
from ..lua_interpreter import lua_interpreter


blp = Blueprint(
    "DeltaAPI", 
    "delta_api", 
    url_prefix="/api", 
    description="DeltaARM Robot Control API - DeltaAPI functions"
)


# ========== Schema Definitions ==========

class DIRequestSchema(Schema):
    """Schema for Digital Input read request."""
    pin = fields.Int(required=True, description="Pin number (1-24)")
    length = fields.Int(required=False, description="Number of consecutive pins to read")


class DORequestSchema(Schema):
    """Schema for Digital Output write request."""
    pin = fields.Int(required=True, description="Pin number (1-12)")
    status = fields.Str(required=True, description="ON or OFF")
    delay = fields.Float(required=False, description="Delay time in seconds")


class ModbusReadSchema(Schema):
    """Schema for Modbus read request."""
    address = fields.Int(required=True, description="Register address (hex or decimal)")
    size = fields.Str(required=True, description="W (16-bit) or DW (32-bit)")


class ModbusWriteSchema(Schema):
    """Schema for Modbus write request."""
    address = fields.Int(required=True, description="Register address (hex or decimal)")
    size = fields.Str(required=True, description="W (16-bit) or DW (32-bit)")
    value = fields.Int(required=True, description="Value to write")


class SetPointSchema(Schema):
    """Schema for SetGlobalPoint request."""
    point_num = fields.Int(required=True, description="Point number (1-1000)")
    name = fields.Str(required=True, description="Point name (must start with GL_)")
    x = fields.Float(required=True, description="X coordinate (mm)")
    y = fields.Float(required=True, description="Y coordinate (mm)")
    z = fields.Float(required=True, description="Z coordinate (mm)")
    rx = fields.Float(required=False, default=0.0, description="RX rotation (degrees)")
    ry = fields.Float(required=False, default=0.0, description="RY rotation (degrees)")
    rz = fields.Float(required=False, default=0.0, description="RZ rotation (degrees)")
    uf = fields.Int(required=False, default=0, description="User frame (0-9)")
    tf = fields.Int(required=False, default=0, description="Tool frame (0-9)")


class ScriptExecuteSchema(Schema):
    """Schema for script execution request."""
    script = fields.Str(required=True, description="Lua script code to execute")


# ========== Digital I/O Endpoints ==========

@blp.route("/di")
class DigitalInputAPI(MethodView):
    """Digital Input API endpoint."""
    
    @blp.arguments(DIRequestSchema)
    @blp.response(200)
    def post(self, args):
        """
        Read Digital Input pin(s).
        
        Returns the status of one or multiple DI pins.
        """
        pin = args['pin']
        length = args.get('length')
        
        if length:
            # Read multiple pins
            result = 0
            for i in range(length):
                if emulator_state.get_di(pin + i):
                    result |= (1 << i)
            return {'pin': pin, 'length': length, 'value': result}
        else:
            # Read single pin
            status = 'ON' if emulator_state.get_di(pin) else 'OFF'
            return {'pin': pin, 'status': status}


@blp.route("/do")
class DigitalOutputAPI(MethodView):
    """Digital Output API endpoint."""
    
    @blp.arguments(DORequestSchema)
    @blp.response(200)
    def post(self, args):
        """
        Set Digital Output pin.
        
        Sets the status of a DO pin, optionally with delay.
        """
        pin = args['pin']
        status = args['status'].upper() == 'ON'
        delay = args.get('delay')
        
        emulator_state.set_do(pin, status)
        
        result = {
            'pin': pin,
            'status': args['status'].upper(),
            'message': f"DO pin {pin} set to {args['status'].upper()}"
        }
        
        if delay:
            import time
            time.sleep(delay)
            emulator_state.set_do(pin, not status)
            result['delayed_status'] = 'OFF' if status else 'ON'
            result['message'] += f" and reversed after {delay}s"
        
        return result
    
    @blp.response(200)
    def get(self):
        """
        Get all Digital Output states.
        
        Returns the current state of all DO pins.
        """
        return {
            'do_states': {
                pin: 'ON' if state else 'OFF' 
                for pin, state in emulator_state.do_state.items()
            }
        }


# ========== Modbus Endpoints ==========

@blp.route("/modbus/read")
class ModbusReadAPI(MethodView):
    """Modbus register read endpoint."""
    
    @blp.arguments(ModbusReadSchema)
    @blp.response(200)
    def post(self, args):
        """
        Read Modbus register.
        
        Reads a 16-bit (W) or 32-bit (DW) value from the specified address.
        """
        address = args['address']
        size = args['size'].upper()
        
        value = emulator_state.read_modbus(address, size)
        
        return {
            'address': f"0x{address:04X}",
            'size': size,
            'value': value
        }


@blp.route("/modbus/write")
class ModbusWriteAPI(MethodView):
    """Modbus register write endpoint."""
    
    @blp.arguments(ModbusWriteSchema)
    @blp.response(200)
    def post(self, args):
        """
        Write Modbus register.
        
        Writes a 16-bit (W) or 32-bit (DW) value to the specified address.
        """
        address = args['address']
        size = args['size'].upper()
        value = args['value']
        
        emulator_state.write_modbus(address, value, size)
        
        return {
            'address': f"0x{address:04X}",
            'size': size,
            'value': value,
            'message': f"Written {value} to address 0x{address:04X}"
        }


# ========== Point Management Endpoints ==========

@blp.route("/point/set")
class SetPointAPI(MethodView):
    """Set global point endpoint."""
    
    @blp.arguments(SetPointSchema)
    @blp.response(200)
    def post(self, args):
        """
        Set a global point.
        
        Stores point data for later use in motion commands.
        """
        point_data = {
            'name': args['name'],
            'x': args['x'],
            'y': args['y'],
            'z': args['z'],
            'rx': args.get('rx', 0.0),
            'ry': args.get('ry', 0.0),
            'rz': args.get('rz', 0.0),
            'uf': args.get('uf', 0),
            'tf': args.get('tf', 0),
            'elbow': 0,
            'shoulder': 0,
            'flip': 0,
            'jrc': [0] * 8
        }
        
        emulator_state.set_global_point(args['point_num'], point_data)
        
        return {
            'point_num': args['point_num'],
            'name': args['name'],
            'message': f"Point {args['point_num']} set successfully"
        }


@blp.route("/point/get/<int:point_num>")
class GetPointAPI(MethodView):
    """Get global point endpoint."""
    
    @blp.response(200)
    def get(self, point_num):
        """
        Get a global point by number.
        
        Retrieves stored point data.
        """
        point_data = emulator_state.get_global_point(point_num)
        
        if point_data:
            return {
                'point_num': point_num,
                'data': point_data
            }
        else:
            return {
                'error': f"Point {point_num} not found"
            }, 404


# ========== Robot State Endpoints ==========

@blp.route("/robot/position")
class RobotPositionAPI(MethodView):
    """Robot position endpoint."""
    
    @blp.response(200)
    def get(self):
        """
        Get current robot position.
        
        Returns the current Cartesian position and orientation.
        """
        return {
            'position': emulator_state.current_position,
            'joint_angles': emulator_state.joint_angles,
            'motion_settings': emulator_state.motion_settings
        }


# ========== Script Execution Endpoint ==========

@blp.route("/script/execute")
class ScriptExecuteAPI(MethodView):
    """Lua script execution endpoint."""
    
    @blp.arguments(ScriptExecuteSchema)
    @blp.response(200)
    def post(self, args):
        """
        Execute a Lua script.
        
        Runs the provided Lua script with access to all DeltaAPI functions.
        Returns execution output and any errors.
        """
        script = args['script']
        
        result = lua_interpreter.execute_script(script)
        
        return {
            'status': result['status'],
            'output': result['output'],
            'error': result['error'],
            'robot_state': {
                'position': emulator_state.current_position,
                'di_state': {k: 'ON' if v else 'OFF' for k, v in emulator_state.di_state.items()},
                'do_state': {k: 'ON' if v else 'OFF' for k, v in emulator_state.do_state.items()}
            }
        }


@blp.route("/script/upload")
class ScriptUploadAPI(MethodView):
    """Lua script file upload endpoint."""
    
    @blp.response(200)
    def post(self):
        """
        Upload and execute a Lua script file.
        
        Accepts a .lua file upload and executes it.
        """
        if 'file' not in request.files:
            return {'error': 'No file provided'}, 400
        
        file = request.files['file']
        
        if file.filename == '':
            return {'error': 'No file selected'}, 400
        
        if not file.filename.endswith('.lua'):
            return {'error': 'File must be a .lua file'}, 400
        
        # Read and execute script
        script_content = file.read().decode('utf-8')
        result = lua_interpreter.execute_script(script_content)
        
        return {
            'filename': file.filename,
            'status': result['status'],
            'output': result['output'],
            'error': result['error']
        }
