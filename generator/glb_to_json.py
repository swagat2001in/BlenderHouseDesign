"""Convert a .glb into a self-contained glTF JSON (buffer embedded as base64).

Web hosts that only serve common file types can serve the .json; three.js's
GLTFLoader reads either form.   python3 generator/glb_to_json.py in.glb out.gltf.json
"""
import base64
import json
import struct
import sys


def convert(src, dst):
    data = open(src, "rb").read()
    magic, _version, _length = struct.unpack_from("<4sII", data, 0)
    assert magic == b"glTF", "not a GLB file"
    off, doc, binbuf = 12, None, b""
    while off < len(data):
        clen, ctype = struct.unpack_from("<I4s", data, off)
        chunk = data[off + 8: off + 8 + clen]
        if ctype == b"JSON":
            doc = json.loads(chunk)
        elif ctype == b"BIN\x00":
            binbuf = chunk
        off += 8 + clen
    doc["buffers"][0]["uri"] = "data:application/octet-stream;base64," + base64.b64encode(binbuf).decode()
    with open(dst, "w") as f:
        json.dump(doc, f, separators=(",", ":"))


if __name__ == "__main__":
    convert(sys.argv[1], sys.argv[2])
