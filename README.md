# Scallop

**Scallop is a Swiss Army Knife for unpacking, repacking, and script stomping (TODO) nodejs single executable applications (SEA)s.**

Use it for source code recovery, malware analysis, or SEA internals exploration.

## Installation

```bash
[TODO] pip install node-sea-scallop
```

## Modes of Operation

### Unpack

Unpack extracts:
1. 🤖 The main javascript bundle from the binary's embedded SEA blob
2. 💾 The main code cache (if it exists) from the binary's embedded SEA blob
3. 🖼️ The embedded assets (if they exist) from the binary's embedded SEA blob
4. 🥩 The raw SEA blob

```bash
scallop unpack <target_sea_binary>
    # Creates target_sea_binary_unpacked in the same directory as target_sea_binary
```

### Repack

Repack replaces the main javascript bundle (or snapshot) with a file of your choosing.

```bash
scallop repack <target_sea_binary> <replacement_js_file_or_snap>
    # Repacks the new content in-place.
```

### [TODO] Repack Assets

TODO