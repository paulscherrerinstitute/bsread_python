import json

import zmq


def zmq_rpc(address, request):
    ctx = zmq.Context()
    sock = zmq.Socket(ctx, zmq.REQ)
    sock.connect(address)

    # assume strings are already JSON encoded
    if not isinstance(request, str):
        request = json.dumps(request)

    sock.send_string(request)

    response = sock.recv_json()

    sock.close()
    ctx.destroy()

    return response



