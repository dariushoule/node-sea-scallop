
from dataclasses import dataclass
from enum import IntEnum, StrEnum
from pathlib import Path
import textwrap
from typing import Dict, Tuple
from rich import print

import lief


class SeaBinaryType(StrEnum):
    PE = "PE"
    ELF = "ELF"
    MACHO = "MACHO_MAN_RANDY_SAVAGE"


class SeaBlobFlags(IntEnum):
    DEFAULT = 0
    DISABLE_EXPERIMENTAL_SEA_WARNING = 1 << 0
    USE_SNAPSHOT = 1 << 1
    USE_CODE_CACHE = 1 << 2
    INCLUDE_ASSETS = 1 << 3


@dataclass
class SeaBlob:
    magic: int
    flags: SeaBlobFlags
    machine_width: int
    code_path: str
    sea_resource: str
    code_cache: bytes | None
    assets: Dict[str, bytes] | None = None
    blob_raw: bytes | None = None

    def __str__(self) -> str:
        flags_str = "DEFAULT" if self.flags == 0 else ", ".join([flag.name for flag in SeaBlobFlags if (flag.value & self.flags)])
        return textwrap.dedent(f"""
        SeaBlob(
            magic={hex(self.magic)},
            flags={hex(self.flags)}, # {flags_str}
            machine_width={self.machine_width},
            code_path="{self.code_path}",
            sea_resource="{self.sea_resource[0:64].replace('\n', '\\n').replace('\r', '\\r')}...",
            code_cache={self.code_cache.hex()[:16] + "..." if len(self.code_cache) > 0 else None},
            assets={self.assets},
            blob_raw={self.code_cache.hex()[:16]}...
        )""").strip()


class SeaBinary:
    def __init__(self, target_binary: Path):
        self.target_binary = target_binary
        with open(target_binary, 'rb') as f:
            self.data = f.read()

    def _file_type(self) -> str:
        if self.data.startswith(b'\x7fELF'):
            return SeaBinaryType.ELF
        elif self.data.startswith(b'MZ'):
            return SeaBinaryType.PE
        elif self.data.startswith(b'\xCF\xFA\xED\xFE') or self.data.startswith(b'\xCE\xFA\xED\xFE'):
            return SeaBinaryType.MACHO
        
    def _extract_pe_blob(self) -> Tuple[lief.PE.Binary, bytes]:
        pe = lief.PE.parse(str(self.target_binary))
        if not pe:
            raise ValueError("Failed to parse PE binary")
        if not pe.resources or len(pe.resources.childs) == 0:
            raise ValueError("No resources found in PE binary, this is not a SEA")
        for dir in pe.resources.childs:
            for leaf in dir.childs:
                if leaf.name == "NODE_SEA_BLOB":
                    return pe, bytes(leaf.childs[0].content)
        raise ValueError("SEA resource not found in PE binary")
    
    @staticmethod
    def _read_uint(b: bytes, ix: int, size=4) -> Tuple[int, int]:
        return int.from_bytes(b[ix:ix+size], byteorder='little'), ix + size
    
    @staticmethod
    def _read_str_view(b: bytes, ix: int, reg_size: int) -> Tuple[str, int]:
        view_size = int.from_bytes(b[ix:ix+reg_size], byteorder='little')
        ix += reg_size
        return b[ix:ix+view_size].decode('utf-8', errors="ignore"), ix + view_size
    
    @staticmethod
    def _read_bytes(b: bytes, ix: int, reg_size: int) -> Tuple[str, int]:
        view_size = int.from_bytes(b[ix:ix+reg_size], byteorder='little')
        ix += reg_size
        return b[ix:ix+view_size], ix + view_size
        
    def unpack_sea_blob(self) -> SeaBlob:
        # https://github.com/nodejs/node/blob/v23.x/src/node_sea.cc#L189

        file_type = self._file_type()
        if file_type == SeaBinaryType.ELF:
            blob = self._extract_elf_blob()
        elif file_type == SeaBinaryType.PE:
            pe, blob = self._extract_pe_blob()
            if pe.header.machine in [
                lief.PE.Header.MACHINE_TYPES.AMD64,
                lief.PE.Header.MACHINE_TYPES.IA64,
                lief.PE.Header.MACHINE_TYPES.ARM64]:
                machine_width = 8
            elif pe.header.machine in [
                lief.PE.Header.MACHINE_TYPES.I386,
                lief.PE.Header.MACHINE_TYPES.ARM,
                lief.PE.Header.MACHINE_TYPES.ARMNT]:
                machine_width = 4
            else:
                raise ValueError("Unsupported PE machine type, support for this architecture is not implemented yet")
            print(f'\t+ Loaded PE-SEA, machine type: {pe.header.machine.name}')
        elif file_type == SeaBinaryType.MACHO:
            blob = self._extract_macho_blob()
        else:
            raise ValueError("Unsupported binary type")
        
        # https://github.com/nodejs/node/blob/v23.x/src/node_sea.cc#L79

        if blob[0:4].hex() != "20da4301":
            raise ValueError("Invalid SEA blob magic number, cannot understand this format")
        
        ix = 0
        magic, ix = self._read_uint(blob, ix, 4)
        flags, ix = self._read_uint(blob, ix, 4)
        code_path, ix = self._read_str_view(blob, ix, machine_width)
        sea_resource, ix = self._read_str_view(blob, ix, machine_width)

        code_cache = None
        if flags & SeaBlobFlags.USE_CODE_CACHE or flags & SeaBlobFlags.USE_SNAPSHOT:
            code_cache, ix = self._read_str_view(blob, ix, machine_width)

        assets = None
        if flags & SeaBlobFlags.INCLUDE_ASSETS:
            assets: Dict[str, bytes] = {}
            n_assets, ix = self._read_uint(blob, ix, machine_width)
            for _ in range(n_assets):
                asset_name, ix = self._read_str_view(blob, ix, machine_width)
                asset_data, ix = self._read_bytes(blob, ix, machine_width)
                assets[asset_name] = asset_data

        return SeaBlob(
            magic=magic,
            flags=flags,
            machine_width=machine_width,
            code_path=code_path,
            sea_resource=sea_resource,
            code_cache=code_cache,
            assets=assets,
            blob_raw=blob,
        )
    
    def _repack_pe_blob(self, repacked: bytes) -> None:
        pe = lief.PE.parse(str(self.target_binary))
        if not pe:
            raise ValueError("Failed to parse PE binary")
        if not pe.resources or len(pe.resources.childs) == 0:
            raise ValueError("No resources found in PE binary, this is not a SEA")
        for dir in pe.resources.childs:
            for leaf in dir.childs:
                if leaf.name == "NODE_SEA_BLOB":
                    leaf.childs[0].content = repacked
                    pe.write(str(self.target_binary))
                    return
        raise ValueError("SEA resource not found in PE binary")
    
    def repack_sea_blob(self, blob: SeaBlob) -> None:
        repacked = bytearray()
        repacked.extend(blob.magic.to_bytes(4, byteorder='little'))
        repacked.extend(blob.flags.to_bytes(4, byteorder='little'))
        repacked.extend(len(blob.code_path).to_bytes(blob.machine_width, byteorder='little'))
        repacked.extend(blob.code_path.encode('utf-8'))
        repacked.extend(len(blob.sea_resource).to_bytes(blob.machine_width, byteorder='little'))
        repacked.extend(blob.sea_resource.encode('utf-8'))
        if blob.flags & SeaBlobFlags.USE_CODE_CACHE or blob.flags & SeaBlobFlags.USE_SNAPSHOT:
            repacked.extend(len(blob.code_cache).to_bytes(blob.machine_width, byteorder='little'))
            repacked.extend(blob.code_cache)
        if blob.flags & SeaBlobFlags.INCLUDE_ASSETS:
            repacked.extend(len(blob.assets).to_bytes(blob.machine_width, byteorder='little'))
            for asset_name, asset_data in blob.assets.items():
                repacked.extend(len(asset_name).to_bytes(blob.machine_width, byteorder='little'))
                repacked.extend(asset_name.encode('utf-8'))
                repacked.extend(len(asset_data).to_bytes(blob.machine_width, byteorder='little'))
                repacked.extend(asset_data)

        file_type = self._file_type()
        if file_type == SeaBinaryType.ELF:
            self._repack_elf_blob()
        elif file_type == SeaBinaryType.PE:
            self._repack_pe_blob(repacked)
        elif file_type == SeaBinaryType.MACHO:
            self._repack_macho_blob()
        else:
            raise ValueError("Unsupported binary type")
