# Scallop

**Scallop is a Swiss Army Knife for unpacking, repacking, and script stomping nodejs single executable applications (SEA)s.**

The project's usage spans source code recovery, malware analysis, red-teaming, and SEA internals exploration.

## Installation

```bash
pip install node-sea-scallop # TODO
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

Important Notes:
1. Output is created in the same directory as `target_sea_binary` under `<target_sea_binary>_unpacked`

### Repack Main Code Resource (without stomping)

Repack replaces the main javascript bundle (or snapshot) with a file of your choosing.

```bash
scallop repack <target_sea_binary> <replacement_js_file_or_v8_snaphot>
```

Important Notes:
1. Content is repacked in-place.
1. Code caches are cleared by default when using this configuration.
2. *If your SEA is code signed, repacking will make the signature invalid. You'll need to be able to resign the binary to make it valid. If your SEA is not codesigned, everything will work as expected.*

### Repack Main Code Resource (with script stomping)

Repack replaces the main javascript bundle (or snapshot) with a file of your choosing.

```bash
scallop repack <target_sea_binary> <replacement_js_file_or_v8_snaphot>
```

Important Notes:
1. Content is repacked in-place.
1. Code caches are cleared by default when using this configuration.
2. *If your SEA is code signed, repacking will make the signature invalid. You'll need to be able to resign the binary to make it valid. If your SEA is not codesigned, everything will work as expected.*

### [TODO] Repack Assets

TODO