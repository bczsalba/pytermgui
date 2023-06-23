"""Interface for interacting with windows api console functions.

The core export is the `enable_virtual_processing` context manager that redirects
console input events and inputs them as ascii codes; this includes mouse input.

Credits:
    - Implementation: [Tired-Fox (Zachary)](https://github.com/Tired-Fox/)
"""

from typing import Any, cast
from enum import Enum
from contextlib import contextmanager
import sys

windll: Any = None
if sys.platform == "win32":
    from ctypes import WinError, byref, LibraryLoader, WinDLL
    from ctypes.wintypes import BOOL, DWORD, HANDLE, LPDWORD

    windll = LibraryLoader(WinDLL)

    # SIGNATURES

    _GetStdHandle = windll.kernel32.GetStdHandle
    _GetStdHandle.argtypes = [DWORD]
    _GetStdHandle.restype = HANDLE

    _GetConsoleMode = windll.kernel32.GetConsoleMode
    _GetConsoleMode.argtypes = [HANDLE, LPDWORD]
    _GetConsoleMode.restype = BOOL

    _SetConsoleMode = windll.kernel32.SetConsoleMode
    _SetConsoleMode.argtypes = [HANDLE, DWORD]
    _SetConsoleMode.restype = BOOL

    # CONSTANTS

    # All input events are redirected to stdin as ansii codes
    ENABLE_VIRTUAL_TERMINAL_INPUT = 0x0200
    # Enable mouse input events
    ENABLE_MOUSE_INPUT = 0x0010
    # Need to be able to enable mouse events
    ENABLE_EXTENDED_FLAGS = 0x0080

    # stdin processes events as ansii codes
    ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
    # Needed for virtual terminal ansii code processing
    ENABLE_PROCESSED_OUTPUT = 0x0001

    # IMPLEMENTATION

    class StdDevice(Enum):
        """The available standard devices for windows."""

        IN = -10
        OUT = -11
        ERR = -12

    def get_std_handle(handle: StdDevice = StdDevice.OUT) -> HANDLE:
        """Retrieves a handle to the specified standard device (stdin, stdout, stderr)

        Args:
            handle (int): Indentifier for the standard device. Defaults to -11 (stdout).

        Returns:
            wintypes.HANDLE: Handle to the standard device
        """
        return cast(HANDLE, _GetStdHandle(handle.value))

    stdout = get_std_handle(StdDevice.OUT)
    stdin = get_std_handle(StdDevice.IN)
    stderr = get_std_handle(StdDevice.ERR)

    def get_console_mode(std: HANDLE) -> DWORD:
        """Get the console mode for the given standard device.

        Args:
            std (HANDLE): The handle to the standard device to get
                the settings from

        Returns:
            False: when setting the mode fails
        """
        mode = DWORD()
        _GetConsoleMode(std, byref(mode))
        return mode

    def set_console_mode(std: HANDLE, mode: int) -> bool:
        """Set the console mode for the given standard device.

        Args:
            std (HANDLE): The handle to the standard device
            mode (int): The mode / setting flags to set to the device

        Returns:
            False when setting the mode fails
        """
        return _SetConsoleMode(std, mode) != 0

    @contextmanager
    def enable_virtual_processing():
        """Context manager that sets windows console input and output settings for
        virtual processing. The console's state is restored when context is lost.

        Enabled:
            Virtual Terminal Input: Input events in the console are converted to ascii codes
            Virtual Processing: Control sequence events are converted and inputed as ascii codes
            Processed Output: Input is parsed for ascii control sequences
            Mouse Input: Mouse events are captured in the console and put into the input buffer
        """

        # Get current console settings for stdin and stdout so they can
        # be reset when the input is done being read
        _old_input_ = get_console_mode(stdin)
        _old_output_ = get_console_mode(stdout)

        try:
            # Set the appropriate settings for input to be converted to ansii
            # and for mouse events to be captured
            if not set_console_mode(
                stdin,
                ENABLE_EXTENDED_FLAGS
                | ENABLE_VIRTUAL_TERMINAL_INPUT
                | ENABLE_MOUSE_INPUT,
            ):
                raise WinError(descr="Failed to set windows console input mode")

            # Set the appropriate settings for output to capture input events as ansii
            if not set_console_mode(
                stdout, ENABLE_PROCESSED_OUTPUT | ENABLE_VIRTUAL_TERMINAL_PROCESSING
            ):
                set_console_mode(stdin, _old_input_.value)
                raise WinError(descr="Failed to set windows console output mode")
            yield
        except Exception as error:
            raise error

        # Done reading input so reset console settings
        if not set_console_mode(stdin, _old_input_.value):
            raise WinError(descr="Failed to set windows console input mode")

        if not set_console_mode(stdout, _old_output_.value):
            raise WinError(descr="Failed to set windows console output mode")


else:

    @contextmanager
    def enable_virtual_processing():
        """Dummy context manager for non windows systems"""
        try:
            yield
        finally:
            pass
