"""
Lua-like Script Interpreter for DeltaARM Robot

This module provides a Lua-compatible scripting interface using lupa (Python-Lua bridge)
and implements all DeltaAPI functions for robot control and I/O operations.
"""

import time
from typing import Any, Union, List, Optional
from lupa import LuaRuntime
from .emulator_state import emulator_state


class LuaInterpreter:
    """Lua interpreter with DeltaAPI function bindings."""
    
    def __init__(self):
        """Initialize the Lua runtime with DeltaAPI functions."""
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self._setup_api()
    
    def _setup_api(self):
        """Setup all DeltaAPI functions in the Lua environment."""
        
        # ========== Digital I/O Functions ==========
        
        def DI(pin_index: Union[int, str], length: Optional[int] = None) -> Union[str, int]:
            """
            Read Digital Input status.
            
            Args:
                pin_index: Pin number (1-24) or name
                length: Optional, number of consecutive pins to read
                
            Returns:
                'ON'/'OFF' for single pin, decimal value for multiple pins
            """
            if length is not None:
                # Read multiple pins and return as decimal
                result = 0
                for i in range(length):
                    pin = pin_index + i
                    if emulator_state.get_di(pin):
                        result |= (1 << i)
                return result
            else:
                # Read single pin
                return 'ON' if emulator_state.get_di(pin_index) else 'OFF'
        
        def DO(pin_index: Union[int, str], status_or_length: Union[str, int], 
               status_num_or_delay: Optional[Union[int, float]] = None,
               delay_time: Optional[float] = None):
            """
            Set Digital Output status.
            
            Multiple signatures:
                DO(pin, status)
                DO(pin, status, delay_time)
                DO(pin, length, status_num)
                DO(pin, length, status_num, delay_time)
            """
            if isinstance(status_or_length, str):
                # Single pin mode: DO(pin, status) or DO(pin, status, delay)
                status = status_or_length.upper() == 'ON'
                emulator_state.set_do(pin_index, status)
                emulator_state.add_log(f"DO({pin_index}, {'ON' if status else 'OFF'})")
                
                if status_num_or_delay is not None:
                    # Delay and reverse
                    time.sleep(status_num_or_delay)
                    emulator_state.set_do(pin_index, not status)
                    emulator_state.add_log(f"DO({pin_index}, {'OFF' if status else 'ON'}) after delay")
            else:
                # Multiple pin mode: DO(pin, length, status_num) or DO(pin, length, status_num, delay)
                length = status_or_length
                status_num = status_num_or_delay
                
                for i in range(length):
                    pin = pin_index + i
                    state = bool((status_num >> i) & 1)
                    emulator_state.set_do(pin, state)
                
                emulator_state.add_log(f"DO({pin_index}, {length}, {status_num})")
                
                if delay_time is not None:
                    time.sleep(delay_time)
                    # Reverse all states
                    for i in range(length):
                        pin = pin_index + i
                        emulator_state.set_do(pin, not emulator_state.get_do(pin))
        
        def ExtDI(address_index: int, pin_index: int) -> str:
            """Read External Digital Input."""
            key = (address_index, pin_index)
            state = emulator_state.ext_di_state.get(key, False)
            return 'ON' if state else 'OFF'
        
        def ExtDO(address_index: int, pin_index: int, status: str, delay_time: Optional[float] = None):
            """Set External Digital Output."""
            key = (address_index, pin_index)
            state = status.upper() == 'ON'
            emulator_state.ext_do_state[key] = state
            emulator_state.add_log(f"ExtDO({address_index}, {pin_index}, {status})")
            
            if delay_time is not None:
                time.sleep(delay_time)
                emulator_state.ext_do_state[key] = not state
        
        # ========== Motion Functions ==========
        
        def MovP(point: Union[int, str], **kwargs):
            """Move to point using joint motion."""
            point_data = emulator_state.get_global_point(point)
            if point_data:
                emulator_state.move_to_position(
                    point_data['x'], point_data['y'], point_data['z'],
                    point_data.get('rx', 0), point_data.get('ry', 0), point_data.get('rz', 0)
                )
                emulator_state.add_log(f"MovP({point}) -> ({point_data['x']}, {point_data['y']}, {point_data['z']})")
            else:
                emulator_state.add_log(f"MovP({point}) - Point not found")
        
        def MovL(point: Union[int, str], **kwargs):
            """Move to point using linear motion."""
            point_data = emulator_state.get_global_point(point)
            if point_data:
                emulator_state.move_to_position(
                    point_data['x'], point_data['y'], point_data['z'],
                    point_data.get('rx', 0), point_data.get('ry', 0), point_data.get('rz', 0)
                )
                emulator_state.add_log(f"MovL({point}) -> ({point_data['x']}, {point_data['y']}, {point_data['z']})")
            else:
                emulator_state.add_log(f"MovL({point}) - Point not found")
        
        def MovJ(joint: int, degree: float, **kwargs):
            """Move single joint to specified angle."""
            if 1 <= joint <= 6:
                emulator_state.joint_angles[joint - 1] = degree
                emulator_state.add_log(f"MovJ(Joint {joint}, {degree}°)")
        
        def SetGlobalPoint(point_num: int, name: str, x: float, y: float, z: float,
                          rx: float = 0.0, ry: float = 0.0, rz: float = 0.0,
                          elbow: int = 0, shoulder: int = 0, flip: int = 0,
                          uf: int = 0, tf: int = 0, jrc: Optional[List] = None):
            """Set a global point."""
            if jrc is None:
                jrc = [0, 0, 0, 0, 0, 0, 0, 0]
            
            point_data = {
                'name': name,
                'x': x, 'y': y, 'z': z,
                'rx': rx, 'ry': ry, 'rz': rz,
                'elbow': elbow, 'shoulder': shoulder, 'flip': flip,
                'uf': uf, 'tf': tf, 'jrc': jrc
            }
            emulator_state.set_global_point(point_num, point_data)
            emulator_state.add_log(f"SetGlobalPoint({point_num}, '{name}', {x}, {y}, {z})")
        
        def ReadPoint(point: Union[int, str], item: str) -> Any:
            """Read point information."""
            point_data = emulator_state.get_global_point(point)
            if not point_data:
                return None
            
            item_map = {
                'X': 'x', 'Y': 'y', 'Z': 'z',
                'RX': 'rx', 'RY': 'ry', 'RZ': 'rz',
                'UF': 'uf', 'TF': 'tf',
                'H': 'hand', 'E': 'elbow', 'S': 'shoulder', 'F': 'flip',
                'JRC': 'jrc'
            }
            
            key = item_map.get(item.upper())
            return point_data.get(key) if key else None
        
        # ========== Speed/Acceleration Settings ==========
        
        def SpdJ(speed: float):
            """Set joint maximum speed (%)."""
            emulator_state.motion_settings['spdj'] = speed
            emulator_state.add_log(f"SpdJ({speed}%)")
        
        def AccJ(acceleration: float):
            """Set joint acceleration (%)."""
            emulator_state.motion_settings['accj'] = acceleration
            emulator_state.add_log(f"AccJ({acceleration}%)")
        
        def DecJ(deceleration: float):
            """Set joint deceleration (%)."""
            emulator_state.motion_settings['decj'] = deceleration
            emulator_state.add_log(f"DecJ({deceleration}%)")
        
        def SpdL(speed: float):
            """Set linear maximum speed (mm/sec)."""
            emulator_state.motion_settings['spdl'] = speed
            emulator_state.add_log(f"SpdL({speed} mm/sec)")
        
        def AccL(acceleration: float):
            """Set linear acceleration (mm/sec²)."""
            emulator_state.motion_settings['accl'] = acceleration
            emulator_state.add_log(f"AccL({acceleration} mm/sec²)")
        
        def DecL(deceleration: float):
            """Set linear deceleration (mm/sec²)."""
            emulator_state.motion_settings['decl'] = deceleration
            emulator_state.add_log(f"DecL({deceleration} mm/sec²)")
        
        def Accur(mode: str, cart: str = "CART"):
            """Set in-place accuracy."""
            emulator_state.motion_settings['accur'] = mode
            emulator_state.add_log(f"Accur({mode})")
        
        # ========== Timing Functions ==========
        
        def WAIT(*args):
            """
            Wait for condition or timeout.
            Supports:
                WAIT(io_type, index, status, [timeout])
                WAIT(var, address, data_type, value)
            """
            if len(args) >= 3:
                if isinstance(args[0], str) and args[0].upper() in ['DI', 'DO']:
                    # Wait for DI/DO
                    io_type = args[0].upper()
                    index = args[1]
                    status = args[2].upper() == 'ON'
                    timeout = args[3] / 1000.0 if len(args) > 3 else None
                    
                    start_time = time.time()
                    emulator_state.add_log(f"WAIT({io_type}, {index}, {'ON' if status else 'OFF'})")
                    
                    while True:
                        if io_type == 'DI':
                            current = emulator_state.get_di(index)
                        else:
                            current = emulator_state.get_do(index)
                        
                        if current == status:
                            break
                        
                        if timeout and (time.time() - start_time) >= timeout:
                            emulator_state.add_log("WAIT timeout")
                            break
                        
                        time.sleep(0.01)
                else:
                    # Wait for Modbus value
                    address = args[1]
                    data_type = args[2]
                    value = args[3]
                    
                    emulator_state.add_log(f"WAIT(Modbus, 0x{address:04X}, {data_type}, {value})")
                    
                    while True:
                        current = emulator_state.read_modbus(address, data_type)
                        if current == value:
                            break
                        time.sleep(0.01)
        
        def DELAY(delay_time: float):
            """Delay execution for specified seconds."""
            emulator_state.add_log(f"DELAY({delay_time}s)")
            time.sleep(delay_time)
        
        # ========== Modbus Functions ==========
        
        def ReadModbus(address: int, size: str) -> int:
            """Read Modbus register."""
            value = emulator_state.read_modbus(address, size)
            emulator_state.add_log(f"ReadModbus(0x{address:04X}, {size}) = {value}")
            return value
        
        def WriteModbus(address: int, size: str, value: int):
            """Write Modbus register."""
            emulator_state.write_modbus(address, value, size)
            emulator_state.add_log(f"WriteModbus(0x{address:04X}, {size}, {value})")
        
        # ========== Utility Functions ==========
        
        def print(*args):
            """Print function for Lua scripts."""
            message = ' '.join(str(arg) for arg in args)
            emulator_state.add_log(f"[PRINT] {message}")
        
        # Register all functions in Lua global namespace
        globals_dict = self.lua.globals()
        
        # I/O Functions
        globals_dict.DI = DI
        globals_dict.DO = DO
        globals_dict.ExtDI = ExtDI
        globals_dict.ExtDO = ExtDO
        
        # Motion Functions
        globals_dict.MovP = MovP
        globals_dict.MovL = MovL
        globals_dict.MovJ = MovJ
        globals_dict.SetGlobalPoint = SetGlobalPoint
        globals_dict.ReadPoint = ReadPoint
        
        # Speed/Acceleration
        globals_dict.SpdJ = SpdJ
        globals_dict.AccJ = AccJ
        globals_dict.DecJ = DecJ
        globals_dict.SpdL = SpdL
        globals_dict.AccL = AccL
        globals_dict.DecL = DecL
        globals_dict.Accur = Accur
        
        # Timing
        globals_dict.WAIT = WAIT
        globals_dict.DELAY = DELAY
        
        # Modbus
        globals_dict.ReadModbus = ReadModbus
        globals_dict.WriteModbus = WriteModbus
        
        # Utility
        globals_dict.print = print
        
        # Constants
        globals_dict.ON = 'ON'
        globals_dict.OFF = 'OFF'
    
    # PUBLIC_INTERFACE
    def execute_script(self, script_code: str) -> dict:
        """
        Execute a Lua script.
        
        Args:
            script_code: Lua script code to execute
            
        Returns:
            Dictionary with execution status and output
        """
        emulator_state.clear_logs()
        emulator_state.script_running = True
        
        try:
            # Execute the Lua script
            self.lua.execute(script_code)
            
            return {
                'status': 'success',
                'output': emulator_state.get_logs(),
                'error': None
            }
        except Exception as e:
            return {
                'status': 'error',
                'output': emulator_state.get_logs(),
                'error': str(e)
            }
        finally:
            emulator_state.script_running = False


# Global interpreter instance
lua_interpreter = LuaInterpreter()
