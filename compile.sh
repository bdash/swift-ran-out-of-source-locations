#!/usr/bin/env bash

SWIFT_ARGS="-parse-as-library -emit-object -Onone -enable-batch-mode -Xfrontend -print-clang-stats @module_maps/module_map_flags.txt"

swiftc $SWIFT_ARGS test.swift
