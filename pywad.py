#!/usr/bin/env python3
# Sheikh Nightshader - WAD Builder/Extractor

import sys
import struct
import re
from pathlib import Path
import argparse

RESET = "\033[0m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"

BANNER = f"""{RED}
   ██████╗  ██████╗  ██████╗ ███╗   ███╗
   ██╔══██╗██╔═══██╗██╔═══██╗████╗ ████║
   ██║  ██║██║   ██║██║   ██║██╔████╔██║
   ██║  ██║██║   ██║██║   ██║██║╚██╔╝██║
   ██████╔╝╚██████╔╝╚██████╔╝██║ ╚═╝ ██║
   ╚═════╝  ╚═════╝  ╚═════╝ ╚═╝     ╚═╝

                Version 1.1
                
"For those who craft Hell itself, one lump at a time"

PyWAD Python WAD Tool - By Sheikh Nightshader
{RESET}
"""

MAP_MARKER_RE = re.compile(r'^(MAP\d{2}|E\dM\d)$', re.IGNORECASE)

def read_order(folder: Path):
    order_file = folder / "order.txt"
    if order_file.exists():
        with open(order_file, "r", encoding="utf-8", errors="ignore") as f:
            return [line.strip() for line in f if line.strip()]
    return [p.name for p in sorted(folder.iterdir()) if p.is_file()]

def collect_folder_blocks(folder: Path):
    order = read_order(folder)
    blocks = []
    nonmap = []
    i = 0
    L = len(order)
    used_names_in_blocks = set()

    while i < L:
        name = order[i]
        path = folder / name
        if not path.exists() or not path.is_file():
            i += 1
            continue

        if MAP_MARKER_RE.match(name):
            block = []
            j = i
            while j < L:
                nm = order[j]
                p = folder / nm
                if j != i and MAP_MARKER_RE.match(nm):
                    break
                if p.exists() and p.is_file():
                    block.append((nm, p.read_bytes()))
                    used_names_in_blocks.add(nm.upper())
                j += 1
            blocks.append(block)
            i = j
        else:
            nonmap.append((name, path.read_bytes()))
            i += 1

    return blocks, nonmap

def build_megawad(folders, out_wad: Path, wad_type="PWAD"):
    folders = [Path(f) for f in folders]
    for f in folders:
        if not f.exists() or not f.is_dir():
            print(f"{RED}[!] Source folder not found:{RESET} {f}")
            return 1

    all_lumps = []
    map_index = 1

    print(f"{CYAN}[*] Building WAD File...{RESET}")
    for folder in folders:
        blocks, nonmap = collect_folder_blocks(folder)
        for block in blocks:
            new_marker = f"MAP{str(map_index).zfill(2)}"
            map_index += 1
            marker_data = block[0][1]
            all_lumps.append((new_marker, marker_data))
            for orig_name, data in block[1:]:
                all_lumps.append((orig_name, data))

    for folder in folders:
        _, nonmap = collect_folder_blocks(folder)
        for name, data in nonmap:
            all_lumps.append((name, data))

    out_wad.parent.mkdir(parents=True, exist_ok=True)
    with open(out_wad, "wb") as f:
        f.write(wad_type.encode("ascii"))
        f.write(struct.pack("<i", len(all_lumps)))
        f.write(struct.pack("<i", 0))

        entries = []
        for name, data in all_lumps:
            filepos = f.tell()
            f.write(data)
            entries.append((filepos, len(data), name))

        dir_offset = f.tell()
        for filepos, size, name in entries:
            nameb = name.encode("ascii", errors="ignore")[:8].ljust(8, b"\0")
            f.write(struct.pack("<i", filepos))
            f.write(struct.pack("<i", size))
            f.write(nameb)

        f.seek(8)
        f.write(struct.pack("<i", dir_offset))

    combined_order = out_wad.with_suffix("").with_name(out_wad.stem + "_order.txt")
    with open(combined_order, "w", encoding="utf-8") as of:
        for _, _, name in entries:
            of.write(f"{name}\n")

    print(f"{GREEN}[*] WAD written:{RESET} {out_wad} ({len(all_lumps)} lumps)")
    return 0

def extract_wad(wad_path: Path, out_folder: Path):
    print(f"{CYAN}[*] Extracting WAD...{RESET}")
    with open(wad_path, "rb") as f:
        header = f.read(4)
        if header not in (b"IWAD", b"PWAD"):
            print(f"{RED}[!] Not a valid WAD.{RESET}")
            return 1
        numlumps = struct.unpack("<i", f.read(4))[0]
        infotableofs = struct.unpack("<i", f.read(4))[0]
        f.seek(infotableofs)
        entries = []
        for _ in range(numlumps):
            data = f.read(16)
            filepos, size, nameb = struct.unpack("<ii8s", data)
            name = nameb.split(b"\0", 1)[0].decode("ascii", errors="ignore")
            entries.append((filepos, size, name))
        out_folder.mkdir(parents=True, exist_ok=True)
        with open(out_folder / "order.txt", "w", encoding="utf-8") as of:
            for _, _, name in entries:
                of.write(f"{name}\n")
        for filepos, size, name in entries:
            f.seek(filepos)
            content = f.read(size)
            with open(out_folder / name, "wb") as wf:
                wf.write(content)
    print(f"{GREEN}[*] Extracted {len(entries)} lumps to:{RESET} {out_folder}")
    return 0

def main():
    print(BANNER)
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    b = sub.add_parser("build")
    b.add_argument("folders", nargs="+", help="Folders (map1_folder map2_folder ...) to merge")
    b.add_argument("out", help="Output WAD filename")
    b.add_argument("--wad-type", choices=["PWAD", "IWAD"], default="PWAD")
    x = sub.add_parser("extract")
    x.add_argument("wad")
    x.add_argument("out")
    args = parser.parse_args()

    if args.cmd == "build":
        return build_megawad(args.folders, Path(args.out), wad_type=args.wad_type)
    elif args.cmd == "extract":
        return extract_wad(Path(args.wad), Path(args.out))
    else:
        parser.print_help()
        return 1

if __name__ == "__main__":
    sys.exit(main())
