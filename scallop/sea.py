
from dataclasses import dataclass
from enum import IntEnum, StrEnum
from pathlib import Path
from typing import Dict, Tuple
from rich import print

import lief
import platform

from scallop.stomp import invalidate_code_cache


NODE_SEA_MAGIC = bytes.fromhex("20da4301")

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
    sea_resource: bytes # Either a source file or a snapshot blob
    code_cache: bytes | None
    assets: Dict[str, bytes] | None = None
    blob_raw: bytes | None = None


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
        
    def _extract_elf_blob(self) -> Tuple[lief.ELF.Binary, bytes]:
        elf = lief.ELF.parse(str(self.target_binary))
        if not elf:
            raise ValueError("Failed to parse ELF binary")
        for section in elf.sections:
            if section.type == lief.ELF.Section.TYPE.NOTE:
                contents = bytes(section.content)
                sentinel = contents.find(b'NODE_SEA_BLOB\x00\x00\x00' + NODE_SEA_MAGIC)
                if sentinel != -1:
                    return elf, contents[sentinel+len(b'NODE_SEA_BLOB\x00\x00\x00'):]
        raise ValueError("SEA resource not found in ELF binary")
        
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
    
    def _extract_macho_blob(self) -> Tuple[lief.MachO.Binary, bytes]:
        fat = lief.MachO.parse(str(self.target_binary))
        if not fat:
            raise ValueError("Failed to parse Mach-O binary")
        
        cpu_type = platform.machine()
        if cpu_type == "arm64":
            macho = fat.take(lief.MachO.Header.CPU_TYPE.ARM64)
        elif cpu_type == "x86_64":
            macho = fat.take(lief.MachO.Header.CPU_TYPE.X86_64)
        elif cpu_type == "i386":
            macho = fat.take(lief.MachO.Header.CPU_TYPE.X86)
        elif cpu_type == "arm":
            macho = fat.take(lief.MachO.Header.CPU_TYPE.ARM)
        else:
            raise ValueError("Unsupported CPU type, support for this architecture is not implemented yet")
        
        if not macho:
            raise ValueError("Failed to parse Mach-O binary")

        for section in macho.sections:
            if section.name == "__NODE_SEA_BLOB":
                return macho, bytes(section.content)
        raise ValueError("SEA resource not found in Mach-O binary, are you on the matching architecture?")
    
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
            elf, blob = self._extract_elf_blob()
            if elf.header.identity_class == lief.ELF.Header.CLASS.ELF32:
                machine_width = 4
            elif elf.header.identity_class == lief.ELF.Header.CLASS.ELF64:
                machine_width = 8
            else:
                raise ValueError("Unsupported ELF class, support for this architecture is not implemented yet")
            print(f'\t+ Loaded ELF-SEA, machine type: {elf.header.identity_class.name}')
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
            _, blob = self._extract_macho_blob()
            cpu_type = platform.machine()
            if cpu_type in ["x86_64", "arm64"]:
                machine_width = 8
            elif cpu_type in ["i386", "arm"]:
                machine_width = 4
            else:
                raise ValueError("Unsupported macho machine type, support for this architecture is not implemented yet")
            print(f'\t+ Loaded MACHO-SEA, machine type: {cpu_type}')
        else:
            raise ValueError("Unsupported binary type")
        
        # https://github.com/nodejs/node/blob/v23.x/src/node_sea.cc#L79

        if blob[0:4].hex() != NODE_SEA_MAGIC.hex():
            raise ValueError("Invalid SEA blob magic number, cannot understand this format")
        
        ix = 0
        magic, ix = self._read_uint(blob, ix, 4)
        flags, ix = self._read_uint(blob, ix, 4)
        code_path, ix = self._read_str_view(blob, ix, machine_width)
        sea_resource, ix = self._read_bytes(blob, ix, machine_width)

        code_cache = None
        if flags & SeaBlobFlags.USE_CODE_CACHE or flags & SeaBlobFlags.USE_SNAPSHOT:
            code_cache, ix = self._read_bytes(blob, ix, machine_width)

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
    
    def _repack_elf_blob(self, repacked: bytes) -> None:
        elf = lief.ELF.parse(str(self.target_binary))
        if not elf:
            raise ValueError("Failed to parse ELF binary")
        for section in elf.sections:
            if section.type == lief.ELF.Section.TYPE.NOTE:
                contents = bytes(section.content)
                sentinel = contents.find(b'NODE_SEA_BLOB\x00\x00\x00' + NODE_SEA_MAGIC)
                if sentinel != -1:
                    new_contents = contents[:sentinel] + b'NODE_SEA_BLOB\x00\x00\x00' + repacked
                    if len(new_contents) < len(contents):
                        new_contents += b'\x00' * (len(contents) - len(new_contents))
                    section.content = [i for i in new_contents]
                    elf.write(str(self.target_binary))
                    return
        raise ValueError("SEA resource not found in ELF binary")
    
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
    
    def _repack_macho_blob(self, repacked: bytes) -> None:
        fat = lief.MachO.parse(str(self.target_binary))
        if not fat:
            raise ValueError("Failed to parse Mach-O binary")
        
        cpu_type = platform.machine()
        if cpu_type == "arm64":
            macho = fat.take(lief.MachO.Header.CPU_TYPE.ARM64)
        elif cpu_type == "x86_64":
            macho = fat.take(lief.MachO.Header.CPU_TYPE.X86_64)
        elif cpu_type == "i386":
            macho = fat.take(lief.MachO.Header.CPU_TYPE.X86)
        elif cpu_type == "arm":
            macho = fat.take(lief.MachO.Header.CPU_TYPE.ARM)
        else:
            raise ValueError("Unsupported CPU type, support for this architecture is not implemented yet")
        
        if not macho:
            raise ValueError("Failed to parse Mach-O binary")

        for section in macho.sections:
            if section.name == "__NODE_SEA_BLOB":
                section.content = repacked
                fat.write(str(self.target_binary))
                return
        raise ValueError("SEA resource not found in Mach-O binary, are you on the matching architecture?")
    
    def repack_sea_blob(self, blob: SeaBlob, stomp_script: bool) -> None:
        if blob.sea_resource.startswith(b'\x19\xdaC\x01'):
            print(f'\t+ Detected v8 snapshot blob, enabling snapshot execution...')
            blob.flags |= SeaBlobFlags.USE_SNAPSHOT

        repacked = bytearray()
        repacked.extend(blob.magic.to_bytes(4, byteorder='little'))
        repacked.extend(blob.flags.to_bytes(4, byteorder='little'))
        repacked.extend(len(blob.code_path).to_bytes(blob.machine_width, byteorder='little'))
        repacked.extend(blob.code_path.encode('utf-8'))
        repacked.extend(len(blob.sea_resource).to_bytes(blob.machine_width, byteorder='little'))
        repacked.extend(blob.sea_resource)
        if blob.flags & SeaBlobFlags.USE_CODE_CACHE:
            if stomp_script:
                # Stomp the included script with the code cache
                if blob.code_cache is None or len(blob.code_cache) == 0:
                    raise ValueError("Stomping is not supported for this SEA blob, there is no code cache")
                repacked.extend(len(blob.code_cache).to_bytes(blob.machine_width, byteorder='little'))
                blob.code_cache = invalidate_code_cache(blob.sea_resource, blob.code_cache)
                repacked.extend(blob.code_cache)
            else:
                print(f'\t+ Detected stale code cache, clearing it...')
                # Clear the code cache, it'll be invalid
                blob.flags &= ~SeaBlobFlags.USE_CODE_CACHE
                repacked[4:8] = blob.flags.to_bytes(4, byteorder='little')
                blob.code_cache = None
        else:
            if stomp_script:
                raise ValueError("Script stomping is not supported in this SEA blob, there is no code cache")
        if blob.flags & SeaBlobFlags.INCLUDE_ASSETS:
            repacked.extend(len(blob.assets).to_bytes(blob.machine_width, byteorder='little'))
            for asset_name, asset_data in blob.assets.items():
                repacked.extend(len(asset_name).to_bytes(blob.machine_width, byteorder='little'))
                repacked.extend(asset_name.encode('utf-8'))
                repacked.extend(len(asset_data).to_bytes(blob.machine_width, byteorder='little'))
                repacked.extend(asset_data)

        file_type = self._file_type()
        if file_type == SeaBinaryType.ELF:
            self._repack_elf_blob(repacked)
        elif file_type == SeaBinaryType.PE:
            self._repack_pe_blob(repacked)
        elif file_type == SeaBinaryType.MACHO:
            self._repack_macho_blob(repacked)
        else:
            raise ValueError("Unsupported binary type")
