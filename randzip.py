#!/usr/bin/env python3
"""
randzip - generate huge text files packed into ONE small zip.

Each file is a single random line repeated over and over. Deflate
compresses that down ~1000:1, so e.g. 60 GB of "random" text can end up
as a ~60 MB zip. Generation is throttled (a short sleep per MB) so it
stays light on CPU/disk, which matters a lot when the total is in the
tens or hundreds of GB.

Nothing here needs anything beyond the Python standard library.

Examples:
  python randzip.py                              # 5 files x 100 MB -> random.zip
  python randzip.py -n 10 -s 1024                 # 10 files x 1 GB
  python randzip.py -n 4 -s 15360 -o huge.zip     # 4 x 15 GB = 60 GB extracted
  python randzip.py -n 1 -s 2097152 --throttle 0  # 1 x 2 TB, no throttle (max load)
"""
import argparse
import base64
import os
import sys
import time
import zipfile

MB = 1024 * 1024


def make_block(block_mb: int) -> bytes:
    """One random text line, repeated to fill `block_mb` megabytes."""
    line = base64.b64encode(os.urandom(48)) + b"\n"  # 65 bytes of random text
    reps = max(1, (block_mb * MB) // len(line))
    return line * reps


def human(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def build_zip(
    out_path: str,
    files: int,
    size_mb: int,
    compresslevel: int,
    throttle: float,
    block_mb: int,
    quiet: bool,
) -> None:
    total_mb = files * size_mb
    with zipfile.ZipFile(
        out_path, "w", zipfile.ZIP_DEFLATED, compresslevel=compresslevel, allowZip64=True
    ) as zf:
        done_mb = 0
        start = time.time()
        for i in range(1, files + 1):
            block = make_block(block_mb)  # a fresh random line per file
            written = 0
            target = size_mb * MB
            with zf.open(f"random_{i:03d}.txt", "w", force_zip64=True) as f:
                while written < target:
                    chunk = block if written + len(block) <= target else block[: target - written]
                    f.write(chunk)
                    written += len(chunk)
                    done_mb += len(chunk) / MB
                    if throttle:
                        time.sleep(throttle)
                    if not quiet:
                        elapsed = time.time() - start
                        pct = done_mb / total_mb * 100
                        sys.stdout.write(
                            f"\r[{i}/{files}] {pct:5.1f}%  {human(done_mb * MB)}/{human(total_mb * MB)}"
                            f"  elapsed {elapsed:6.0f}s   "
                        )
                        sys.stdout.flush()
        if not quiet:
            print()


def main():
    ap = argparse.ArgumentParser(
        description="Generate huge repeated-line text files packed into one small zip.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    ap.add_argument("-o", "--out", default="random.zip", help="output zip path")
    ap.add_argument("-n", "--files", type=int, default=5, help="number of text files")
    ap.add_argument("-s", "--size-mb", type=int, default=100, help="size of EACH file, in MB")
    ap.add_argument(
        "-c", "--compress-level", type=int, default=9, choices=range(0, 10),
        metavar="0-9", help="deflate level (9 = smallest zip, 0 = store/no compression)",
    )
    ap.add_argument(
        "-t", "--throttle", type=float, default=0.003,
        help="seconds to sleep per MB written; raise to lower load further, 0 for max speed",
    )
    ap.add_argument(
        "--block-mb", type=int, default=1,
        help="size of the repeated block held in memory per file, in MB",
    )
    ap.add_argument("-q", "--quiet", action="store_true", help="no progress output")
    ap.add_argument(
        "-y", "--yes", action="store_true", help="skip the confirmation prompt for large jobs"
    )
    args = ap.parse_args()

    total_mb = args.files * args.size_mb
    sleep_s = total_mb * args.throttle
    print(
        f"Plan: {args.files} file(s) x {human(args.size_mb * MB)} = {human(total_mb * MB)} extracted\n"
        f"Compression level: {args.compress_level}  |  Throttle: {args.throttle}s/MB "
        f"(~{sleep_s / 60:.1f} min of pure throttling, plus actual I/O/compression time)\n"
        f"Output: {args.out}"
    )
    if total_mb * MB > 50 * 1024 * MB and not args.yes:  # > ~50 GB
        reply = input("That's a large job and may take a while. Continue? [y/N] ")
        if reply.strip().lower() not in ("y", "yes"):
            print("Aborted.")
            return

    start = time.time()
    build_zip(
        args.out, args.files, args.size_mb, args.compress_level,
        args.throttle, args.block_mb, args.quiet,
    )
    elapsed = time.time() - start
    zip_size = os.path.getsize(args.out)
    print(
        f"Done in {elapsed:.1f}s. {args.out} is {human(zip_size)} "
        f"(extracts to {human(total_mb * MB)})."
    )


if __name__ == "__main__":
    main()
