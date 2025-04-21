#!/usr/bin/env bash

source ~/.profile
./asset/build-node22.sh
./asset/build-node23.sh
./snap/build-node22.sh
./snap/build-node23.sh
./stomp/build-node22.sh
./stomp/build-node23.sh
./test1/build-node22.sh
./test1/build-node23.sh