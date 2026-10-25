"""Minimal stdlib PNG read/write (8-bit RGB/RGBA/indexed/grey), so the texture tool needs no Pillow."""
import struct, zlib

def read(data):
    assert data[:8] == b'\x89PNG\r\n\x1a\n'
    pos, idat, plte, trns = 8, b'', None, None
    while pos < len(data):
        n, t = struct.unpack('>I4s', data[pos:pos + 8]); body = data[pos + 8:pos + 8 + n]; pos += 12 + n
        if t == b'IHDR': w, h, depth, ctype = struct.unpack('>IIBB', body[:10])
        elif t == b'PLTE': plte = [tuple(body[i:i + 3]) for i in range(0, len(body), 3)]
        elif t == b'tRNS': trns = body
        elif t == b'IDAT': idat += body
    assert depth == 8 or (depth in (1, 2, 4) and ctype in (0, 3)), f'bit depth {depth} unsupported'
    ch = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ctype]
    bpp = max(1, ch * depth // 8)  # filter byte distance
    stride = (w * ch * depth + 7) // 8
    raw, prev, rows = zlib.decompress(idat), bytearray(stride), []
    for y in range(h):
        f, line = raw[y * (stride + 1)], bytearray(raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
        for i in range(stride):
            a = line[i - bpp] if i >= bpp else 0; b = prev[i]; c = prev[i - bpp] if i >= bpp else 0
            if f == 1: line[i] = (line[i] + a) & 255
            elif f == 2: line[i] = (line[i] + b) & 255
            elif f == 3: line[i] = (line[i] + (a + b) // 2) & 255
            elif f == 4:
                p = a + b - c; pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[i] = (line[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        prev = line
        if depth < 8:  # unpack sub-byte samples to one per byte
            per, mask = 8 // depth, (1 << depth) - 1
            line = bytearray((line[x // per] >> (8 - depth * (x % per + 1))) & mask for x in range(w))
            if ctype == 0: line = bytearray(v * 255 // mask for v in line)
        rows.append(line)
    px = []
    for line in rows:
        r = []
        for x in range(w):
            v = line[x * ch:(x + 1) * ch]
            if ctype == 6: r.append(tuple(v))
            elif ctype == 2: r.append((*v, 255))
            elif ctype == 0: r.append((v[0],) * 3 + (255,))
            elif ctype == 4: r.append((v[0],) * 3 + (v[1],))
            else: r.append((*plte[v[0]], trns[v[0]] if trns and v[0] < len(trns) else 255))
        px.append(r)
    return px

def write(path, px):
    h, w = len(px), len(px[0])
    raw = b''.join(b'\x00' + bytes(c for p in row for c in p) for row in px)
    chunk = lambda t, b: struct.pack('>I', len(b)) + t + b + struct.pack('>I', zlib.crc32(t + b) & 0xffffffff)
    with open(path, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0))
                + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))
