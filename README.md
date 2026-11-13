# randzip

Generate huge text files packed into **one small zip**, without hammering
your CPU or disk.

Each generated file is a single random line repeated over and over.
Deflate compresses that down roughly **1000:1**, so a 60 GB request can
end up as a ~60 MB zip file — while still extracting to the full size on
disk. Generation is throttled (a short sleep per MB written) so it stays
light on load even for very large totals.

Pure Python standard library — no dependencies, no `pip install`.

## Usage

```bash
python randzip.py                              # 5 files x 100 MB -> random.zip
python randzip.py -n 10 -s 1024                 # 10 files x 1 GB
python randzip.py -n 4 -s 15360 -o huge.zip     # 4 x 15 GB = 60 GB extracted
python randzip.py -n 1 -s 2097152 --throttle 0  # 1 x 2 TB, no throttle (max speed/load)
```

Before it starts, it prints the plan (file count, size each, total, rough
time) and, for anything over ~50 GB, asks you to confirm.

## Options

| Flag | Default | Meaning |
|---|---|---|
| `-o, --out` | `random.zip` | output zip path |
| `-n, --files` | `5` | number of text files to generate |
| `-s, --size-mb` | `100` | size of **each** file, in MB (so total = files × size-mb) |
| `-c, --compress-level` | `9` | deflate level 0–9 (9 = smallest zip, 0 = store/no compression, less CPU) |
| `-t, --throttle` | `0.003` | seconds to sleep per MB written — raise to reduce load further, `0` for max speed |
| `--block-mb` | `1` | size of the repeated block kept in memory per file, in MB |
| `-q, --quiet` | off | suppress the progress line |
| `-y, --yes` | off | skip the confirmation prompt on large jobs |

## How big, how long?

- **Zip size:** roughly `total_size / 1000`, since it's all one repeated
  line per file and deflate eats that easily.
- **Time:** dominated by the throttle setting. At the default
  `0.003s` per MB, 1 TB takes about 50 minutes of pure throttling, on top
  of the (much smaller) actual write/compress time. Set `--throttle 0` to
  go as fast as the disk/CPU allow, at the cost of full load.
- **Disk while running:** only the final (tiny) zip is written — there's
  no multi-GB temp file, since each file streams straight into the zip
  as it's generated.
- **Disk after extracting:** the full, real size — a 60 GB request really
  does need 60 GB free to unzip.

## Why repeated lines instead of fully random data?

Fully random bytes don't compress at all, so a 60 GB zip of real random
data would need ~60 GB of disk and a lot of CPU to write. Repeating one
random line per file keeps the zip tiny and the generation cheap, while
still giving you files that extract to whatever size you asked for — useful
for testing storage limits, upload/download behavior, backup tooling, etc.
on data you don't need to be truly random.

## License

MIT — see [LICENSE](LICENSE).
