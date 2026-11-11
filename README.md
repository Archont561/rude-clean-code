# Offline sandbox (orphan branch)

Built 2026-11-11T17:17:04Z from commit `87927c1` for platform `linux-64`.
`pixi.lock` sha256 `5fca8d4474d77b1b31b5e4b0f482869814ca66b346b8c9e1b15b0921fd1b9d8f`.

The verified self-bootstrap binary is stored at `.pixi-sandbox/tools/linux-64/pixi-sandbox`. The branch root intentionally contains documentation only.

| env | platform | packed | unpacked | files |
| --- | --- | ---: | ---: | ---: |
| `default` | linux-64 | 160.5 MiB | 525.0 MiB | 121 |


## Restore on the disconnected machine

```bash
./.pixi-sandbox/tools/linux-64/pixi-sandbox doctor --branch-location . --verify
./.pixi-sandbox/tools/linux-64/pixi-sandbox restore --branch-location . --output-path <project> --force
# then, from <project> with no network, use pixi as the sole entrypoint:
pixi install --frozen --offline
pixi run --frozen -- cargo build --offline
```

Every manifest blob is verified before it is written into the working tree.
