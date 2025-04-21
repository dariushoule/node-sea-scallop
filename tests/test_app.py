from pathlib import Path
import shutil
import subprocess
from typer.testing import CliRunner

from scallop.cli import app
from tests.util import clear_unpacked_repacked

runner = CliRunner()


NODE_BUILD_VERSION = "build-node22"


def test_unpack_test1_win32():
    clear_unpacked_repacked("test1")
    result = runner.invoke(app, ["unpack", f"tests/seas/test1/{NODE_BUILD_VERSION}/test1.exe"])
    assert result.exit_code == 0, result.output
    assert "Unpacked successfully!" in result.stdout
    assert Path(f'tests/seas/test1/{NODE_BUILD_VERSION}/test1_unpacked').exists()
    assert Path(f'tests/seas/test1/{NODE_BUILD_VERSION}/test1_unpacked/raw_sea.blob').exists()
    assert Path(f'tests/seas/test1/{NODE_BUILD_VERSION}/test1_unpacked/dist_bundle.js').exists()
    clear_unpacked_repacked("test1")


def test_repack_test1_win32():
    clear_unpacked_repacked("test1")
    shutil.copyfile(
        f"tests/seas/test1/{NODE_BUILD_VERSION}/test1.exe",
        f"tests/seas/test1/{NODE_BUILD_VERSION}/test1_repacked.exe"
    )

    result = runner.invoke(app, ["unpack", f"tests/seas/test1/{NODE_BUILD_VERSION}/test1.exe"])
    assert result.exit_code == 0, result.output

    with Path(f'tests/seas/test1/{NODE_BUILD_VERSION}/test1_unpacked/dist_bundle.js').open('rb') as f:
        dist_bundle = f.read()
        dist_bundle = dist_bundle.replace(b"Hello, world!", b"Hello, scallop!")

    with Path(f'tests/seas/test1/{NODE_BUILD_VERSION}/test1_unpacked/dist_bundle.js').open('wb') as f:
        f.write(dist_bundle)

    result = runner.invoke(app, ["repack", f"tests/seas/test1/{NODE_BUILD_VERSION}/test1_repacked.exe", 
                                 f"tests/seas/test1/{NODE_BUILD_VERSION}/test1_unpacked/dist_bundle.js"])
    assert result.exit_code == 0, result.output
    assert "Repacked successfully!" in result.stdout

    out = subprocess.check_output(
        [f"tests/seas/test1/{NODE_BUILD_VERSION}/test1_repacked.exe"], stderr=subprocess.STDOUT
    ).decode("utf-8")

    assert "Hello, scallop!" in out
    clear_unpacked_repacked("test1")


def test_repack_stomp_js_win32():
    clear_unpacked_repacked("stomp")
    shutil.copyfile(
        f"tests/seas/stomp/{NODE_BUILD_VERSION}/stomp.exe",
        f"tests/seas/stomp/{NODE_BUILD_VERSION}/stomp_repacked.exe"
    )

    result = runner.invoke(app, ["unpack", f"tests/seas/stomp/{NODE_BUILD_VERSION}/stomp.exe"])
    assert result.exit_code == 0, result.output

    with Path(f'tests/seas/stomp/{NODE_BUILD_VERSION}/stomp_unpacked/src_main.js').open('wb') as f:
        f.write(b'console.log("abc123456");')

    result = runner.invoke(app, ["repack", f"tests/seas/stomp/{NODE_BUILD_VERSION}/stomp_repacked.exe", 
                                 f"tests/seas/stomp/{NODE_BUILD_VERSION}/stomp_unpacked/src_main.js",
                                 "--stomp"])
    assert result.exit_code == 0, result.output
    assert "Repacked successfully!" in result.stdout

    out = subprocess.check_output(
        [f"tests/seas/stomp/{NODE_BUILD_VERSION}/stomp_repacked.exe"], stderr=subprocess.STDOUT
    ).decode("utf-8")

    assert "abc123456" not in out
    assert "stompystomp" in out

    with Path(f"tests/seas/stomp/{NODE_BUILD_VERSION}/stomp_repacked.exe").open("rb") as f:
        data = f.read()
        assert b"abc123456" in data
    clear_unpacked_repacked("stomp")


def test_repack_no_stomp_js_win32():
    clear_unpacked_repacked("stomp")
    shutil.copyfile(
        f"tests/seas/stomp/{NODE_BUILD_VERSION}/stomp.exe",
        f"tests/seas/stomp/{NODE_BUILD_VERSION}/stomp_repacked.exe"
    )

    result = runner.invoke(app, ["unpack", f"tests/seas/stomp/{NODE_BUILD_VERSION}/stomp.exe"])
    assert result.exit_code == 0, result.output

    with Path(f'tests/seas/stomp/{NODE_BUILD_VERSION}/stomp_unpacked/src_main.js').open('wb') as f:
        f.write(b'console.log("abc123456");')

    result = runner.invoke(app, ["repack", f"tests/seas/stomp/{NODE_BUILD_VERSION}/stomp_repacked.exe", 
                                 f"tests/seas/stomp/{NODE_BUILD_VERSION}/stomp_unpacked/src_main.js"])
    assert result.exit_code == 0, result.output
    assert "Repacked successfully!" in result.stdout

    out = subprocess.check_output(
        [f"tests/seas/stomp/{NODE_BUILD_VERSION}/stomp_repacked.exe"], stderr=subprocess.STDOUT
    ).decode("utf-8")

    assert "abc123456" in out
    assert "stompystomp" not in out
    clear_unpacked_repacked("stomp")


def test_repack_snapshot_win32():
    clear_unpacked_repacked("test1")
    clear_unpacked_repacked("snap")
    shutil.copyfile(
        f"tests/seas/test1/{NODE_BUILD_VERSION}/test1.exe",
        f"tests/seas/test1/{NODE_BUILD_VERSION}/test1_repacked.exe"
    )

    result = runner.invoke(app, ["unpack", f"tests/seas/snap/{NODE_BUILD_VERSION}/snap.exe"])
    assert result.exit_code == 0, result.output

    result = runner.invoke(app, ["repack", f"tests/seas/test1/{NODE_BUILD_VERSION}/test1_repacked.exe", 
                                 f"tests/seas/snap/{NODE_BUILD_VERSION}/snap_unpacked/src_index.js"])
    assert result.exit_code == 0, result.output
    assert "Detected v8 snapshot blob" in result.stdout
    assert "Repacked successfully!" in result.stdout

    out = subprocess.check_output(
        [f"tests/seas/test1/{NODE_BUILD_VERSION}/test1_repacked.exe"], stderr=subprocess.STDOUT
    ).decode("utf-8")

    assert "snapsnap" in out
    assert "Hello, world!" not in out

    clear_unpacked_repacked("snap")
    clear_unpacked_repacked("test1")


def test_repack_asset_win32():
    clear_unpacked_repacked("asset")
    shutil.copyfile(
        f"tests/seas/asset/{NODE_BUILD_VERSION}/asset.exe",
        f"tests/seas/asset/{NODE_BUILD_VERSION}/asset_repacked.exe"
    )

    result = runner.invoke(app, ["unpack", f"tests/seas/asset/{NODE_BUILD_VERSION}/asset.exe"])
    assert result.exit_code == 0, result.output

    with Path(f'tests/seas/asset/{NODE_BUILD_VERSION}/asset_unpacked/payload_abc_txt').open('wb') as f:
        f.write(b'zzz')

    result = runner.invoke(app, ["repack-asset", f"tests/seas/asset/{NODE_BUILD_VERSION}/asset_repacked.exe",
                                 "payload/abc.txt",
                                 f"tests/seas/asset/{NODE_BUILD_VERSION}/asset_unpacked/payload_abc_txt"])
    assert result.exit_code == 0, result.output
    assert "Repacked asset successfully!" in result.stdout
    assert "Adding or replacing asset" in result.stdout

    out = subprocess.check_output(
        [f"tests/seas/asset/{NODE_BUILD_VERSION}/asset_repacked.exe"], stderr=subprocess.STDOUT
    ).decode("utf-8")
    out = out.replace("\r\n", "\n")  # Normalize line endings

    assert "zzz" in out
    assert "abc\nabc\nabc" not in out
    assert "def\ndef\ndef" in out
    clear_unpacked_repacked("asset")


def test_repack_asset_new_win32():
    clear_unpacked_repacked("asset")
    shutil.copyfile(
        f"tests/seas/asset/{NODE_BUILD_VERSION}/asset.exe",
        f"tests/seas/asset/{NODE_BUILD_VERSION}/asset_repacked.exe"
    )

    result = runner.invoke(app, ["unpack", f"tests/seas/asset/{NODE_BUILD_VERSION}/asset.exe"])
    assert result.exit_code == 0, result.output

    with Path(f'tests/seas/asset/{NODE_BUILD_VERSION}/asset_unpacked/payload_abc_txt').open('wb') as f:
        f.write(b'zzz')

    result = runner.invoke(app, ["repack-asset", f"tests/seas/asset/{NODE_BUILD_VERSION}/asset_repacked.exe",
                                 "payload/zzz.txt",
                                 f"tests/seas/asset/{NODE_BUILD_VERSION}/asset_unpacked/payload_abc_txt"])
    assert result.exit_code == 0, result.output
    assert "Repacked asset successfully!" in result.stdout
    assert "Adding or replacing asset" in result.stdout

    out = subprocess.check_output(
        [f"tests/seas/asset/{NODE_BUILD_VERSION}/asset_repacked.exe"], stderr=subprocess.STDOUT
    ).decode("utf-8")
    out = out.replace("\r\n", "\n")  # Normalize line endings

    assert "zzz" not in out
    with Path(f"tests/seas/asset/{NODE_BUILD_VERSION}/asset_repacked.exe").open("rb") as f:
        data = f.read()
        assert b"payload/zzz.txt" in data
    assert "abc\nabc\nabc" in out
    assert "def\ndef\ndef" in out
    clear_unpacked_repacked("asset")
