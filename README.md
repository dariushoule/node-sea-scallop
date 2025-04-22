# Scallop: The Node SEA Swiss Army Knife

<p align="center"><img src="https://github.com/dariushoule/node-sea-scallop/blob/main/scallop.png" alt="scallop"></p>

**Scallop is a multi-tool for unpacking, repacking, and script stomping nodejs single executable applications (SEA)s.**

The project serves source code recovery, malware analysis, red-teaming, and SEA internals exploration.

**Compatibility Matrix**

| OS      | Node Version | Unpack | Repack | Stomp | Repack Asset |
|---------|--------------|--------|--------|-------|--------------|
| Windows |           23 |      ✅|    ✅ |    ✅ |          ✅ |
| Windows |           22 |      ✅|    ✅ |    ✅ |          ✅ |
| Linux   |           23 |      ✅|    ✅ |    ✅ |          ✅ |
| Linux   |           22 |      ✅|    ✅ |    ✅ |          ✅ |
| MacOS¹  |           23 |      ✅|    ✅ |    ✅ |          ✅ |
| MacOS¹  |           22 |      ✅|    ✅ |    ✅ |          ✅ |

¹ On MacOS, repacked binaries will not execute unless they are re-codesigned or manually excluded from codesigning.

## Installation

```bash
pip install node-sea-scallop

scallop --help
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
```

Important Notes:
1. Output is created in the same directory as `target_sea_binary` under `<target_sea_binary>_unpacked/`


### Repack Main Code Resource (without stomping)

Repack replaces the main javascript bundle (or snapshot) with a file of your choosing.

```bash
scallop repack <target_sea_binary> <replacement_js_file_or_v8_snapshot>
```

Important Notes:
1. Content is repacked in-place.
2. The Code cache is cleared by default when using this configuration.
3. *If your SEA is code signed, repacking will make the signature invalid. You'll need to be able to resign the binary to make it valid. If your SEA is not codesigned, everything will work as expected.*


### Repack Main Code Resource (script stomped)

Repack replaces the main javascript bundle (or snapshot) with a file of your choosing. The script is stomped by the code cache. 

```bash
scallop repack <target_sea_binary> <replacement_js_file_or_v8_snaphot> --stomp
```

Important Notes:
1. Content is repacked in-place.
2. The Code cache is NOT cleared when using this configuration, and _will_ be executed preferentially.
    - The code cache's `kSourceHash` is recalculated to allow v8's `SanityCheckJustSource` check to pass. 
3. The target binary must have a code cache to be stompable.
4. *If your SEA is code signed, repacking will make the signature invalid. You'll need to be able to resign the binary to make it valid. If your SEA is not codesigned, everything will work as expected.*


#### Footnote: A Few Words on Script Stomping 🥾

nodejs stores main code resources as either a plaintext string or a near-plaintext V8 snapshot inside its SEA blob. Along side the code, there is an optional bytecode cache that can be used to speed up compilation and execution. Assuming  source and bytecode pass sanity checks the bytecode will be used preferentially to the main code resource for execution. 

By keeping the bytecode cache intact and replacing the main code resource, a desynchronization between source and bytecode is created. This allows a SEA to disguise the true intent of its main code resource, and stealth its logic behind a harder-to-reverse-engineer serialized v8 bytecode blob.

The implications are not altogether that different than the classic VBA/P-code Stomp: [https://attack.mitre.org/techniques/T1564/007/](https://attack.mitre.org/techniques/T1564/007/)

I personally have used script stomped node SEAs as a very effective C2 implant delivery mechanism during red-team engagements. EDRs are not yet well clued into script stomping in SEAs.


### Repack Asset

Repack asset replaces a specific asset with a file of your choosing, creating it if it does not exist.

```bash
scallop repack-asset <target_sea_binary> <replacement_asset_name> <replacement_asset_file>
```

Important Notes:
1. Content is repacked in-place.
2. The Code cache is cleared by default when using this configuration.
3. *If your SEA is code signed, repacking will make the signature invalid. You'll need to be able to resign the binary to make it valid. If your SEA is not codesigned, everything will work as expected.*
