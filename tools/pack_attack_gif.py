
"""Combine GIF frames made by System.Drawing without recompressing their palettes."""
import argparse
from pathlib import Path
from struct import pack


def subblocks_end(data, start):
    while data[start]:
        start += 1 + data[start]
    return start + 1


def palette_end(start, flags):
    return start + (3 << (1 + (flags & 7))) if flags & 0x80 else start


def frame(data):
    if data[:6] not in (b'GIF87a', b'GIF89a'):
        raise ValueError('Expected a GIF frame')
    global_end = palette_end(13, data[10])
    start = global_end
    while data[start] == 0x21:
        start = subblocks_end(data, start + 2)
    if data[start] != 0x2C:
        raise ValueError('GIF frame has no image descriptor')
    descriptor = bytearray(data[start:start + 10])
    start += 10
    local_flags = descriptor[9]
    if local_flags & 0x80:
        end = palette_end(start, local_flags)
        palette = data[start:end]
        start = end
        colors = local_flags & 7
    else:
        palette = data[13:global_end]
        colors = data[10] & 7
    descriptor[9] = (local_flags & 0x40) | 0x80 | colors
    end = subblocks_end(data, start + 1)
    return data[6:global_end], descriptor, palette, data[start:end]


def write_clip(files, output):
    with output.open('wb') as gif:
        screen_size = None
        for index, file in enumerate(files):
            header, descriptor, palette, pixels = frame(file.read_bytes())
            if index == 0:
                screen_size = header[:4]
                gif.write(b'GIF89a' + header + b'\x21\xff\x0bNETSCAPE2.0\x03\x01\x00\x00\x00')
            elif screen_size != header[:4]:
                raise ValueError(f'Inconsistent GIF frame size: {file}')
            # Round to the closest centisecond at 30 frames per second.
            delay = round((index + 1) * 100 / 30) - round(index * 100 / 30)
            gif.write(b'\x21\xf9\x04\x04' + pack('<H', delay) + b'\x00\x00')
            gif.write(descriptor + palette + pixels)
        gif.write(b'\x3b')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('frames', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    files = sorted(args.frames.glob('*.gif'))
    if not files:
        parser.error('No GIF frames found')
    write_clip(files, args.output)
