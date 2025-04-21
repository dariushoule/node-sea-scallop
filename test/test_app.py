from pathlib import Path
import shutil
import subprocess
from typer.testing import CliRunner

from scallop.cli import app
from test.util import clear_unpacked_repacked

runner = CliRunner()


def test_unpack_test1():
    clear_unpacked_repacked("test1")
    result = runner.invoke(app, ["unpack", "test/seas/test1/build-node23/test1.exe"])
    assert result.exit_code == 0, result.output
    assert "Unpacked successfully!" in result.stdout
    assert Path('test/seas/test1/build-node23/test1_unpacked').exists()
    assert Path('test/seas/test1/build-node23/test1_unpacked/raw_sea.blob').exists()
    assert Path('test/seas/test1/build-node23/test1_unpacked/dist_bundle.js').exists()
    clear_unpacked_repacked("test1")


def test_repack_test1():
    clear_unpacked_repacked("test1")
    shutil.copyfile(
        "test/seas/test1/build-node23/test1.exe",
        "test/seas/test1/build-node23/test1_repacked.exe"
    )

    result = runner.invoke(app, ["unpack", "test/seas/test1/build-node23/test1.exe"])
    assert result.exit_code == 0

    with Path('test/seas/test1/build-node23/test1_unpacked/dist_bundle.js').open('rb') as f:
        dist_bundle = f.read()
        dist_bundle = dist_bundle.replace(b"Hello, world!", b"Hello, scallop!")

    with Path('test/seas/test1/build-node23/test1_unpacked/dist_bundle.js').open('wb') as f:
        f.write(dist_bundle)

    result = runner.invoke(app, ["repack", "test/seas/test1/build-node23/test1_repacked.exe", 
                                 "test/seas/test1/build-node23/test1_unpacked/dist_bundle.js"])
    assert result.exit_code == 0, result.output
    assert "Repacked successfully!" in result.stdout

    out = subprocess.check_output(
        ["test/seas/test1/build-node23/test1_repacked.exe"], stderr=subprocess.STDOUT
    ).decode("utf-8")

    assert "Hello, scallop!" in out
    clear_unpacked_repacked("test1")


def test_repack_stomp_js():
    clear_unpacked_repacked("stomp")
    shutil.copyfile(
        "test/seas/stomp/build-node23/stomp.exe",
        "test/seas/stomp/build-node23/stomp_repacked.exe"
    )

    result = runner.invoke(app, ["unpack", "test/seas/stomp/build-node23/stomp.exe"])
    assert result.exit_code == 0

    with Path('test/seas/stomp/build-node23/stomp_unpacked/src_main.js').open('wb') as f:
        f.write(b'console.log("abc123456");')

    result = runner.invoke(app, ["repack", "test/seas/stomp/build-node23/stomp_repacked.exe", 
                                 "test/seas/stomp/build-node23/stomp_unpacked/src_main.js"])
    assert result.exit_code == 0, result.output
    assert "Repacked successfully!" in result.stdout

    out = subprocess.check_output(
        ["test/seas/stomp/build-node23/stomp_repacked.exe"], stderr=subprocess.STDOUT
    ).decode("utf-8")

    assert "abc123456" not in out
    assert "stompystomp" in out

    with Path("test/seas/stomp/build-node23/stomp_repacked.exe").open("rb") as f:
        data = f.read()
        assert b"abc123456" in data
    clear_unpacked_repacked("stomp")
