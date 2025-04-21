from pathlib import Path
import re
import typer
from rich import print

from scallop.sea import SeaBinary, SeaBlobFlags


app = typer.Typer()


@app.command(help="Unpack a node SEA")
def unpack(target_binary: str):
    print(":oyster: scallop started in [bold]UNPACK[/bold] mode :oyster:\n")
    target_binary_p = Path(target_binary)
    if not target_binary_p.is_file():
        raise typer.BadParameter(f"File {target_binary} does not exist, or is not a file.")
    print(f"[bold][yellow]* Unpacking '{target_binary}'...[/yellow][/bold]")
    sb = SeaBinary(target_binary_p)
    sea_blob = sb.unpack_sea_blob()
    extract_dir = target_binary_p.parent / f'{target_binary_p.stem}_unpacked'
    extract_dir.mkdir(exist_ok=True)

    target = (extract_dir / f'raw_sea.blob')
    print(f"[bold]\t* Extracting raw SEA blob to '{target}'...[/bold]")
    with (extract_dir / f'raw_sea.blob').open('wb') as f:
        f.write(sea_blob.blob_raw)

    santized_code_path = re.sub(r'[^a-zA-Z0-9_-]', '_', sea_blob.code_path)
    santized_code_path = re.sub(r'_js$', '.js', santized_code_path)
    target = (extract_dir / f'{santized_code_path}')
    print(f"[bold]\t* Extracting main resource to '{target}'...[/bold]")
    with target.open('wb') as f:
        f.write(sea_blob.sea_resource.encode('utf-8'))

    if sea_blob.code_cache:
        target = (extract_dir / f'code_cache.bin')
        print(f"[bold]\t* Extracting code cache to '{target}'...[/bold]")
        with target.open('wb') as f:
            f.write(sea_blob.code_cache)

    if sea_blob.assets:
        for asset_name, asset_data in sea_blob.assets.items():
            santized_asset_name = re.sub(r'[^a-zA-Z0-9_-]', '_', asset_name)
            target = (extract_dir / f'{santized_asset_name}')
            print(f"[bold]\t* Extracting asset '{asset_name}' to '{target}'...[/bold]")
            with target.open('wb') as f:
                f.write(asset_data)

    print("[green][bold]+ Unpacked successfully![/bold][/green] :tada:")


@app.command(help="Repack a node SEA")
def repack(target_binary: str, target_script: str, code_cache: str = None):
    print(":oyster: scallop started in [bold]REPACK[/bold] mode :oyster:\n")
    target_binary_p = Path(target_binary)
    if not target_binary_p.is_file():
        raise typer.BadParameter(f"File {target_binary} does not exist, or is not a file.")
    print(f"[bold][yellow]* Loading '{target_binary}'...[/yellow][/bold]")
    sb = SeaBinary(target_binary_p)
    sea_blob = sb.unpack_sea_blob()

    target_script_p = Path(target_script)
    if not target_script_p.is_file():
        raise typer.BadParameter(f"File {target_script} does not exist, or is not a file.")
    print(f"[bold][yellow]* Replacing main script with '{target_script}'...[/yellow][/bold]")
    with target_script_p.open('r') as f:
        sea_blob.sea_resource = f.read()

    if code_cache:
        code_cache_p = Path(code_cache)
        if not code_cache_p.is_file():
            raise typer.BadParameter(f"File {code_cache} does not exist, or is not a file.")
        print(f"[bold][yellow]* Loading code cache '{code_cache}'...[/yellow][/bold]")
        with code_cache_p.open('rb') as f:
            sea_blob.code_cache = f.read()
    else:
        sea_blob.code_cache = None
    sea_blob.flags &= ~SeaBlobFlags.USE_CODE_CACHE

    sb.repack_sea_blob(sea_blob)
    print("[green][bold]+ Repacked successfully![/bold][/green] :tada:")


@app.command(help="Repack a node SEA asset")
def repack_asset(target_binary: str, target_asset_name: str, target_asset: str):
    print(":oyster: scallop started in [bold]REPACK ASSET[/bold] mode :oyster:\n")
    target_binary_p = Path(target_binary)
    if not target_binary_p.is_file():
        raise typer.BadParameter(f"File {target_binary} does not exist, or is not a file.")
    print(f"[bold][yellow]* Loading '{target_binary}'...[/yellow][/bold]")
    sb = SeaBinary(target_binary_p)
    sea_blob = sb.unpack_sea_blob()

    target_asset_p = Path(target_asset)
    if not target_asset_p.is_file():
        raise typer.BadParameter(f"File {target_asset} does not exist, or is not a file.")
    
    print(f"[bold][yellow]* Adding or replacing asset '{target_asset_name}' with '{target_asset}'...[/yellow][/bold]")
    with target_asset_p.open('rb') as f:
        sea_blob.assets[target_asset_name] = f.read()
    sea_blob.flags |= SeaBlobFlags.INCLUDE_ASSETS

    sb.repack_sea_blob(target_binary_p, sea_blob)
    print("[green][bold]+ Repacked asset successfully![/bold][/green] :tada:")


if __name__ == "__main__":
    app()
