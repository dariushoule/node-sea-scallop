#!/usr/bin/env bash

workdir="$(dirname $0)"
pushd $workdir
eval $(fnm env)
fnm use 23.11.0
node --experimental-sea-config sea-config.json

if [[ "$OSTYPE" == "linux"* ]]; then
    outfile="stomp.elf"
    dest="$outfile"
    cp "$(command -v node)" $dest
    npx -y postject $dest NODE_SEA_BLOB sea.blob --sentinel-fuse NODE_SEA_FUSE_fce680ab2cc467b6e072b8b5df1996b2
elif [[ "$OSTYPE" == "darwin"* ]]; then
    outfile="stomp.macho"
    dest="$outfile"
    cp "$(command -v node)" $dest
    codesign --remove-signature $dest
    npx -y postject $dest NODE_SEA_BLOB sea.blob --sentinel-fuse NODE_SEA_FUSE_fce680ab2cc467b6e072b8b5df1996b2 --macho-segment-name NODE_SEA 
fi

rm -rf "$workdir/build-node23"
mkdir -p "$workdir/build-node23"
mv sea.blob "$workdir/build-node23/sea.blob"
mv $dest "$workdir/build-node23/$outfile"
popd