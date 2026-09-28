import socket
def test_no_network():
    try:
        socket.create_connection(("1.1.1.1", 53), timeout=3)
    except OSError:
        return
    raise AssertionError("network is reachable")
