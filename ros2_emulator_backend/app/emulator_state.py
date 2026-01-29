"""
DeltaARM Robot Emulator State Management

This module manages the internal state of the simulated DeltaARM robot,
including digital I/O, Modbus registers, motion settings, and robot positions.
"""

import threading
from typing import Dict, List, Union, Any, Optional


class EmulatorState:
    """Singleton class to manage the emulator's state across all requests."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the emulator state if not already initialized."""
        if self._initialized:
            return
            
        # Digital Input state (24 pins, 1-24)
        self.di_state: Dict[int, bool] = {i: False for i in range(1, 25)}
        
        # Digital Output state (12 pins, 1-12)
        self.do_state: Dict[int, bool] = {i: False for i in range(1, 13)}
        
        # External DI/DO state (by address and pin)
        self.ext_di_state: Dict[tuple, bool] = {}
        self.ext_do_state: Dict[tuple, bool] = {}
        
        # Modbus registers (address range 0x1000-0x1FFF, 0x3000-0x3FFF)
        self.modbus_registers: Dict[int, int] = {}
        
        # Robot position state (6-axis: X, Y, Z, RX, RY, RZ)
        self.current_position = {
            'x': 0.0,
            'y': 0.0,
            'z': 0.0,
            'rx': 0.0,
            'ry': 0.0,
            'rz': 0.0
        }
        
        # Joint angles (6 joints)
        self.joint_angles = [0.0] * 6
        
        # Global points storage (1-1000)
        self.global_points: Dict[int, Dict[str, Any]] = {}
        
        # Motion settings
        self.motion_settings = {
            'spdj': 10.0,  # Joint speed %
            'accj': 10.0,  # Joint acceleration %
            'decj': 10.0,  # Joint deceleration %
            'spdl': 100.0,  # Linear speed mm/sec
            'accl': 10.0,  # Linear acceleration mm/sec²
            'decl': 10.0,  # Linear deceleration mm/sec²
            'accur': 'HIGH'  # In-place accuracy
        }
        
        # Script execution state
        self.script_output: List[str] = []
        self.script_running = False
        
        self._initialized = True
    
    # PUBLIC_INTERFACE
    def get_di(self, pin: int) -> bool:
        """
        Get the state of a Digital Input pin.
        
        Args:
            pin: Pin number (1-24)
            
        Returns:
            True if ON, False if OFF
        """
        if pin not in self.di_state:
            return False
        return self.di_state[pin]
    
    # PUBLIC_INTERFACE
    def set_di(self, pin: int, state: bool):
        """
        Set the state of a Digital Input pin (for simulation purposes).
        
        Args:
            pin: Pin number (1-24)
            state: True for ON, False for OFF
        """
        if 1 <= pin <= 24:
            self.di_state[pin] = state
    
    # PUBLIC_INTERFACE
    def get_do(self, pin: int) -> bool:
        """
        Get the state of a Digital Output pin.
        
        Args:
            pin: Pin number (1-12)
            
        Returns:
            True if ON, False if OFF
        """
        if pin not in self.do_state:
            return False
        return self.do_state[pin]
    
    # PUBLIC_INTERFACE
    def set_do(self, pin: int, state: bool):
        """
        Set the state of a Digital Output pin.
        
        Args:
            pin: Pin number (1-12)
            state: True for ON, False for OFF
        """
        if 1 <= pin <= 12:
            self.do_state[pin] = state
    
    # PUBLIC_INTERFACE
    def read_modbus(self, address: int, size: str = 'W') -> int:
        """
        Read a Modbus register.
        
        Args:
            address: Register address (0x1000-0x1FFF, 0x3000-0x3FFF)
            size: 'W' for 16-bit, 'DW' for 32-bit
            
        Returns:
            Register value
        """
        if size == 'DW':
            # Read 32-bit value from two consecutive registers
            low = self.modbus_registers.get(address, 0)
            high = self.modbus_registers.get(address + 1, 0)
            return (high << 16) | (low & 0xFFFF)
        else:
            return self.modbus_registers.get(address, 0)
    
    # PUBLIC_INTERFACE
    def write_modbus(self, address: int, value: int, size: str = 'W'):
        """
        Write to a Modbus register.
        
        Args:
            address: Register address (0x1000-0x1FFF, 0x3000-0x3FFF)
            value: Value to write
            size: 'W' for 16-bit, 'DW' for 32-bit
        """
        if size == 'DW':
            # Write 32-bit value to two consecutive registers
            self.modbus_registers[address] = value & 0xFFFF
            self.modbus_registers[address + 1] = (value >> 16) & 0xFFFF
        else:
            self.modbus_registers[address] = value & 0xFFFF
    
    # PUBLIC_INTERFACE
    def set_global_point(self, point_num: int, data: Dict[str, Any]):
        """
        Store a global point.
        
        Args:
            point_num: Point number (1-1000)
            data: Point data dictionary
        """
        if 1 <= point_num <= 1000:
            self.global_points[point_num] = data
    
    # PUBLIC_INTERFACE
    def get_global_point(self, point: Union[int, str]) -> Optional[Dict[str, Any]]:
        """
        Retrieve a global point by number or name.
        
        Args:
            point: Point number or point name
            
        Returns:
            Point data dictionary or None
        """
        if isinstance(point, int):
            return self.global_points.get(point)
        else:
            # Search by name
            for p_data in self.global_points.values():
                if p_data.get('name') == point:
                    return p_data
            return None
    
    # PUBLIC_INTERFACE
    def move_to_position(self, x: float, y: float, z: float, 
                        rx: float = 0.0, ry: float = 0.0, rz: float = 0.0):
        """
        Simulate moving the robot to a position.
        
        Args:
            x, y, z: Cartesian coordinates in mm
            rx, ry, rz: Rotation angles in degrees
        """
        self.current_position = {
            'x': x, 'y': y, 'z': z,
            'rx': rx, 'ry': ry, 'rz': rz
        }
    
    # PUBLIC_INTERFACE
    def add_log(self, message: str):
        """
        Add a log message to the script output.
        
        Args:
            message: Log message
        """
        self.script_output.append(message)
    
    # PUBLIC_INTERFACE
    def clear_logs(self):
        """Clear all script output logs."""
        self.script_output = []
    
    # PUBLIC_INTERFACE
    def get_logs(self) -> List[str]:
        """
        Get all script output logs.
        
        Returns:
            List of log messages
        """
        return self.script_output.copy()


# Global instance
emulator_state = EmulatorState()
