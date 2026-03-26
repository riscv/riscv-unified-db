#!/usr/bin/env ruby
# frozen_string_literal: true

# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

require 'json'

ext = JSON.load_file('.vscode/extensions.json')['recommendations']
dev = JSON.load_file('.devcontainer/devcontainer.json')['customizations']['vscode']['extensions']

if ext.sort != dev.sort
  only_in_extensions = ext - dev
  only_in_devcontainer = dev - ext

  puts 'Mismatch between .vscode/extensions.json["recommendations"] and .devcontainer/devcontainer.json["customizations"]["vscode"]["extensions"]'
  unless only_in_extensions.empty?
    puts "  Present only in .vscode/extensions.json: #{only_in_extensions.inspect}"
  end
  unless only_in_devcontainer.empty?
    puts "  Present only in .devcontainer/devcontainer.json: #{only_in_devcontainer.inspect}"
  end

  exit 1
end
