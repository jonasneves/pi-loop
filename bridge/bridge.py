"""PTY ↔ BLE Nordic UART bridge. Runs a child command under a PTY and mirrors
the PTY's output to the NUS TX (notify) characteristic; NUS RX (writable) writes
go back into the PTY. That writable+notify pair is exactly what tab-device's
property-bind discovers — so tab-device needs zero changes.

NUS is low-bandwidth (~244 B MTU), so notifications are chunked to 20 B — the
size tab-device assumes. BlueZ starts late in boot, so this is never a boot
console; the USB-gadget serial is the recovery path when this is down.

BLE peripheral via `bless`. If bless advertising proves flaky on the Pi's BlueZ,
the fallback is dbus-next directly (same GATT shape, more boilerplate)."""
import asyncio
import os
import pty
import sys

NUS_SERVICE = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
NUS_RX = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"  # host → device (writable)
NUS_TX = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"  # device → host (notify)
MTU_CHUNK = 20


def chunk(data: bytes, size: int):
    for i in range(0, len(data), size):
        yield data[i:i + size]


async def run_bridge(command: list[str], ble_name: str) -> None:
    from bless import (BlessServer, BlessGATTCharacteristicProperties,
                       GATTCharacteristicProperties, GATTAttributePermissions)

    pid, master_fd = pty.fork()
    if pid == 0:  # child: become the command
        os.execvp(command[0], command)
        os._exit(127)

    server = BlessServer(name=ble_name)

    def on_write(_char, value, **_):
        os.write(master_fd, bytes(value))  # RX → PTY stdin

    server.write_request_func = on_write
    await server.add_new_service(NUS_SERVICE)
    await server.add_new_characteristic(
        NUS_SERVICE, NUS_RX,
        GATTCharacteristicProperties.write | GATTCharacteristicProperties.write_without_response,
        None, GATTAttributePermissions.writeable)
    await server.add_new_characteristic(
        NUS_SERVICE, NUS_TX,
        GATTCharacteristicProperties.notify, None,
        GATTAttributePermissions.readable)
    await server.start()

    loop = asyncio.get_running_loop()

    def pump_pty():
        try:
            data = os.read(master_fd, 256)  # PTY stdout → TX notify
        except OSError:
            return
        for c in chunk(data, MTU_CHUNK):
            server.get_characteristic(NUS_TX).value = c
            server.update_value(NUS_SERVICE, NUS_TX)

    loop.add_reader(master_fd, pump_pty)
    # Run until the child exits.
    await loop.run_in_executor(None, os.waitpid, pid, 0)
    await server.stop()


def _parse_argv(argv):
    # bridge.py -- cmd arg arg
    sep = argv.index("--")
    return argv[sep + 1:]


if __name__ == "__main__":
    cmd = _parse_argv(sys.argv)
    asyncio.run(run_bridge(cmd, os.environ.get("BLE_NAME", "piloop")))
