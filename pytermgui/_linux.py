"""
Helper functions for Linux and Unix-like platforms
"""

from __future__ import annotations

from contextlib import contextmanager
from termios import (
    CSIZE,
    tcgetattr,
    tcsetattr,
    TCSANOW,
    TCSAFLUSH,
    TCSADRAIN,
    ECHO,
    BRKINT,
    ICRNL,
    INPCK,
    ISTRIP,
    IXON,
    VMIN,
    VTIME,
    CS8,
    ICANON,
    PARENB,
    OPOST,
    IEXTEN,
    ISIG
)
from sys import stdin, stdout
from typing import IO, Callable, Generator

from .helpers import export

IFLAG: int = 0
OFLAG: int = 1
CFLAG: int = 2
LFLAG: int = 3
ISPEED: int = 4
OSPEED: int = 5
CC: int = 6

@export
def echo_on(file: IO | None = None) -> None:
    """Turns on ECHO"""

    if not file:
        file = stdin
    file_descriptor: int = file.fileno()
    term_attributes: list = tcgetattr(file_descriptor)
    term_attributes[LFLAG] |= ECHO
    tcsetattr(file_descriptor, TCSANOW, term_attributes)

@export
def echo_off(file: IO | None = None) -> None:
    """Turns off ECHO"""

    if not file:
        file = stdin
    file_descriptor: int = file.fileno()
    term_attributes: list = tcgetattr(file_descriptor)
    term_attributes[LFLAG] &= ~ECHO
    tcsetattr(file_descriptor, TCSANOW, term_attributes)

@export
def set_raw(
    file_descriptor: int | None = None,
    when: int = TCSAFLUSH
) -> None:
    """Puts `file_descriptor` into `raw` mode

    Args:
        file_descriptor (int | None, optional): File descriptor. Defaults to None.
        when (int, optional): When. Defaults to TCSAFLUSH.
    """

    if not file_descriptor:
        file_descriptor: int = stdin.fileno()
    mode: list = tcgetattr(file_descriptor)
    mode[IFLAG] &= ~(BRKINT | ICRNL | INPCK | ISTRIP | IXON)
    mode[OFLAG] &= ~(OPOST)
    mode[CFLAG] &= ~(CSIZE | PARENB)
    mode[CFLAG] |= CS8
    mode[LFLAG] &= ~(ECHO | ICANON | IEXTEN | ISIG)
    mode[CC][VMIN] = 1
    mode[CC][VTIME] = 0
    tcsetattr(file_descriptor, when, mode)

@export
def set_cbreak(
    file_descriptor: int | None = None,
    when: int = TCSAFLUSH
) -> None:
    """Puts `file_descriptor` into `cbreak` mode

    Args:
        file_descriptor (int | None, optional): File descriptor. Defaults to None.
        when (int, optional): When. Defaults to TCSAFLUSH.
    """

    if not file_descriptor:
        file_descriptor: int = stdin.fileno()
    mode: list = tcgetattr(file_descriptor)
    mode[LFLAG] &= ~(ECHO | ICANON)
    mode[CC][VMIN] = 1
    mode[CC][VTIME] = 0
    tcsetattr(file_descriptor, when, mode)

@export
@contextmanager
def raw(file_descriptor: int | None = None, when: int = TCSAFLUSH) -> Generator[None]:
    """
    Context manager for `raw` mode

    Args:
        file_descriptor (int, optional): File descriptor. Defaults to None.
        when (int, optional): When. Defaults to TCSAFLUSH.

    Yields:
        Generator[None]: Nothing
    """

    if not file_descriptor:
        file_descriptor: int = stdin.fileno()
    old_settings: list = tcgetattr(file_descriptor)
    set_raw(file_descriptor, when)
    try:
        yield
    finally:
        tcsetattr(file_descriptor, old_settings)

@export
@contextmanager
def cbreak(file_descriptor: int | None = None, when: int = TCSAFLUSH) -> Generator[None]:
    """
    Context manager for `cbreak` mode

    Args:
        file_descriptor (int, optional): File descriptor. Defaults to None.
        when (int, optional): When. Defaults to TCSAFLUSH.

    Yields:
        Generator[None]: Nothing
    """

    if not file_descriptor:
        file_descriptor: int = stdin.fileno()
    old_settings: list = tcgetattr(file_descriptor)
    set_cbreak(file_descriptor, when)
    try:
        yield
    finally:
        tcsetattr(file_descriptor, old_settings)

@export
@contextmanager
def noecho(file: IO | None = None) -> Generator[None]:
    """
    Context manager for `noecho` mode

    Args:
        file (IO, optional): I/O file. Defaults to None.

    Yields:
        Generator[None]: Nothing
    """

    echo_off(file)
    try:
        yield
    finally:
        echo_on(file)

@export
@contextmanager
def echo(file: IO | None = None) -> Generator[None]:
    """
    Context manager for `echo` mode

    Args:
        file (IO, optional): I/O file. Defaults to None.

    Yields:
        Generator[None]: Nothing
    """

    echo_on(file)
    try:
        yield
    finally:
        echo_off(file)

@export
def getch(echo_: bool = False, timeout: int = 0) -> str | None:
    """
    Gets a single unbuffered character from standard input.

    Args:
        echo (bool, optional): Print character on screen. Defaults to False.
        timeout (int, optional): Time to wait before cancelling.
            <=0 is Infinite. Defaults to 0 (Infinity).

    Returns:
        str: Single unbuffered character
    """

    file_descriptor: int = stdin.fileno()
    old_settings: list = tcgetattr(file_descriptor)
    mode: list = old_settings
    try:
        mode[IFLAG] &= ~(BRKINT | ICRNL | INPCK | ISTRIP | IXON)
        mode[OFLAG] &= ~(OPOST)
        mode[CFLAG] &= ~(CSIZE | PARENB)
        mode[CFLAG] |= CS8
        mode[LFLAG] &= ~(ECHO | ICANON | IEXTEN | ISIG)
        mode[CC][VMIN] = 1
        mode[CC][VTIME] = max(timeout, 0)
        tcsetattr(file_descriptor, TCSAFLUSH, mode)
        char: str | None = stdin.read(1)
    finally:
        tcsetattr(file_descriptor, TCSADRAIN, old_settings)
    if echo_:
        stdout.write(char)
    return char

@export
def getkey(
    getch_: Callable[[bool, int], str] = getch,
    echo_: bool = False,
    timeout: int = 0,
) -> str | None:
    """
    Get a single character on Linux. if an extended key is pressed, key is returned

    Args:
        getch_ (Callable[[bool, int], str], optional): Char getter function. Defaults to getch.
        echo_ (bool, optional): Echo result. Defaults to False.
        timeout (int, optional): Timeout in - seconds. <=0 is Infinite . Defaults to 0 (Infinite)

    Returns:
        str | None: key or None
    """

    result: str = (char1 := getch_(..., timeout))
    if ord(char1) == 0x1B:
        result += (char2 := getch_())
        if ord(char2) == 0x5B:
            result += (char3 := getch_())
            if ord(char3) == 0x33:
                result += getch_()
    if echo_:
        stdout.write(result)
    return result
