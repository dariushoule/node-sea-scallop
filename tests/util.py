from pathlib import Path
import shutil

def clear_unpacked_repacked(name: str):
    unpacked_dir = Path(__file__).parent / f'seas/{name}/build-node23/{name}_unpacked'
    if unpacked_dir.is_dir():
        shutil.rmtree(unpacked_dir)
    repacked = Path(__file__).parent / f'seas/{name}/build-node23/{name}_repacked.exe'
    if repacked.is_file():
        repacked.unlink()
