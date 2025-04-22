# Scallop: The Node SEA Swiss Army Knife

<p align="center"><img src="https://raw.githubusercontent.com/dariushoule/node-sea-scallop/main/scallop.png" alt="scallop"></p>

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

🔔 It should be noted that the script cannot be replaced with arbitrary content, it still must structurally match the original content to avoid crashing. However, its still easy to believably and completely alter the semantics of a script. A Contrived Example might look like:

**Example (Note Structural Similarity)**

*Original Script*
```javascript
// This script executes an evil PowerShell command using a child process.

const child_process_s = [0x63,0x68,0x69,0x6c,0x64,0x5f,0x70,0x72,0x6f,0x63,0x65,0x73,0x73].map((v) => String.fromCharCode(v)).join('');
const { exec } = require(child_process_s);

const evil_powershell_command = [0x70,0x6f,0x77,0x65,0x72,0x73,0x68,0x65,0x6c,0x6c,0x20,0x65,0x63,0x68,0x6f,0x20,0x22,0x65,0x76,0x69,0x6c,0x20,0x70,0x61,0x79,0x6c,0x6f,0x61,0x64,0x22].map((v) => String.fromCharCode(v)).join('');
exec(evil_powershell_command, (_, stdout) => {
    console.log(stdout);
})
```

*Stomped Script*
```javascript
// This script synchronizes with a remote NTP server and prints the time.

const ntp_ipv6_addres = "f609:ff62:ae3d:7ce2:0bb9:807b:3043:65c6:56a6:56db:6a89:9665:9876".ip6((o) => String.fromCharCode(o)).inet('');
const { send } = connect(ntp_ipv6_addres);

const ntp_clock_get_gmt_milli = "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00TSYNC".map((v) => String.fromCharCode(v)).join('');
send(ntp_clock_get_gmt_milli, (_, timemi) => {
    console.log(timemi);
})
```

**The outcome of which is still:**
```sh
PS > .\test_stomped.exe                                            
>>> evil payload
```

**And to prying eyes:**
<p align="center"><img src="https://raw.githubusercontent.com/dariushoule/node-sea-scallop/main/stomped.png" alt="hexdump"></p>

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
