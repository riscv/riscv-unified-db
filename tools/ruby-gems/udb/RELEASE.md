<!--
Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
SPDX-License-Identifier: CC0-1.0
-->


# Releasing the `udb` gem

This document describes how to prepare and publish a release of the `udb` gem to
[rubygems.org](https://rubygems.org).

> **Automated releases:** The publish step (Steps 2–4 below) is handled
> automatically by the
> [Release udb gem to RubyGems.org](../../.github/workflows/release_udb_gem.yml)
> GitHub Actions workflow.  Simply bump the version in `version.rb`, commit,
> and merge to `main` — the workflow will build, publish, and tag the release.
> Manual publishing (Steps 2–4) is only needed if the CI workflow is unavailable.

---

## Overview

The `udb` gem is developed inside the `riscv-unified-db` monorepo but is
distributed as a standalone gem.  Because the gem code references RISC-V
specification data that lives in `spec/` and `cfgs/` of the monorepo, the
release process copies that data into a `.data/` directory inside a staging
copy of the gem before building the `.gem` file.

The high-level steps are:

1. Bump the version.
2. Run `bin/chore build udb-gem` to create a staging directory and build the `.gem` file.
3. Push the `.gem` file to rubygems.org.

---

## Prerequisites

* Ruby and Bundler available in your `PATH` (the repo's `bin/` wrappers or a
  system install both work).
* A rubygems.org account with push rights to the `udb` gem, and an API key
  configured in `~/.gem/credentials`.

---

## Step 1 – Bump the version

Edit `tools/ruby-gems/udb/lib/udb/version.rb` and update the version string:

```ruby
module Udb
  def self.version = "X.Y.Z"
end
```

Commit the change and tag the commit:

```sh
git add tools/ruby-gems/udb/lib/udb/version.rb
git commit -m "chore(udb): bump gem version to X.Y.Z"
git tag udb-vX.Y.Z
```

---

## Step 2 – Build the gem

Run the following command from the repository root:

```sh
bin/chore build udb-gem
```

This will:

1. Prepare a self-contained staging directory at `<repo-root>/gen/udb_gem/`
   by copying the gem source tree and populating `.data/` with the
   specification data the gem needs at runtime:

   | Source (monorepo)       | Destination in staging          |
   |-------------------------|---------------------------------|
   | `spec/std/isa/`         | `.data/spec/std/isa/`           |
   | `spec/custom/isa/`      | `.data/spec/custom/isa/`        |
   | `spec/schemas/`         | `.data/spec/schemas/`           |
   | `cfgs/`                 | `.data/cfgs/`                   |

2. Run `gem build udb.gemspec` inside the staging directory.
3. Print the path to the built `.gem` file.

To use a different staging directory, pass `-d DIR`:

```sh
bin/chore build udb-gem -d /tmp/udb_gem_staging
```

The underlying Rake task (`rake release:udb:prepare`) can also be run
directly if needed; the `UDB_GEM_GEN_DIR` environment variable overrides
the staging directory in that case.

---

## Step 3 – Smoke-test the built gem (optional but recommended)

Install the gem into a temporary sandbox and verify the CLI works:

```sh
SANDBOX=$(mktemp -d)
GEM_HOME=$SANDBOX GEM_PATH=$SANDBOX:$(ruby -e 'puts Gem.path.join(":")') \
  gem install --no-document udb-X.Y.Z.gem

GEM_HOME=$SANDBOX GEM_PATH=$SANDBOX:$(ruby -e 'puts Gem.path.join(":")') \
  $SANDBOX/bin/udb list extensions
```

The command should print a list of RISC-V extensions without errors.

---

## Step 4 – Push to rubygems.org

```sh
gem push udb-X.Y.Z.gem
```

---

## Automated testing

The unit test `tools/ruby-gems/udb/test/test_gem_install.rb` exercises the
full prepare → build → install → run cycle automatically.  Run it with:

```sh
rake test:udb:unit
```

or directly:

```sh
cd tools/ruby-gems/udb
ruby -Ilib:test test/run.rb
```
