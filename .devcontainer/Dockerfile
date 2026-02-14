FROM ubuntu:24.04@sha256:cd1dba651b3080c3686ecf4e3c4220f026b521fb76978881737d24f200828b2b
LABEL org.opencontainers.image.source=https://github.com/riscv/riscv-unified-db

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /workspace

# please keep pkgs sorted
RUN apt-get update && \
  apt-get install -y --no-install-recommends --fix-missing \
  bash-completion \
  build-essential \
  clang-format \
  clang-tidy \
  curl \
  ditaa \
  g++ \
  gcc-riscv64-linux-gnu \
  gcc-riscv64-unknown-elf \
  gdb \
  git \
  gpg \
  gpg-agent \
  less \
  libc6-dev-riscv64-cross \
  libelf-dev \
  libgmp-dev \
  libnewlib-dev \
  libyaml-dev \
  libz3-dev \
  minisat \
  parallel \
  ssh \
  sudo \
  zlib1g-dev \
  \
  && apt-get clean autoclean \
  && apt-get autoremove -y \
  && rm -rf /var/lib/{apt,dpkg,cache,log}/*

# Install mise for tool management
# See: https://mise.jdx.dev/mise-cookbook/docker.html
ENV MISE_DATA_DIR="/mise"
ENV MISE_CONFIG_DIR="/mise"
ENV MISE_CACHE_DIR="/mise/cache"
ENV MISE_STATE_DIR="/mise/state"
ENV MISE_INSTALL_PATH="/usr/local/bin/mise"
ENV MISE_YES=1
ENV MISE_TRUSTED_CONFIG_PATHS="/"
ENV UV_CACHE_DIR="/tmp/uv-cache"
ENV PATH="/mise/shims:$PATH"
RUN curl https://mise.run | sh

# Install tools managed by mise (.mise.toml)
COPY .mise.toml /mise/config.toml
# Install rust first — needed during Ruby compilation for YJIT
RUN mise install rust
RUN mise install
RUN mise reshim
RUN mkdir -p /mise/state && chmod -R 777 /mise

# build/install eqntott
RUN git clone --depth=1 https://github.com/TheProjecter/eqntott.git && \
    cd eqntott && \
    ./configure && \
    make && make install && \
    cd .. && \
    rm -rf eqntott

# build/install espresso
RUN git clone --depth=1 https://github.com/psksvp/espresso-ab-1.0.git && \
    cd espresso-ab-1.0 && \
    ./configure && \
    make && make install && \
    cd .. && \
    rm -rf espresso-ab-1.0

# build / install must
# mcsmus/mcsmus/control.cc is missing #include <cstdio>, thus the sed below
RUN git clone https://github.com/jar-ben/mustool.git && \
    cd mustool && \
    git checkout 17fa9f9542a9ce05328dfccd1cd410f05f741ab3 && \
    sed -i -e 's/#include <signal.h>/#include <signal.h>\n#include <cstdio>/' mcsmus/mcsmus/control.cc && \
    make -j && \
    install must -m 0777 /usr/bin/must && \
    cd .. && \
    rm -rf mustool

# Sync Python project dependencies with uv
COPY pyproject.toml uv.lock /opt/python/
RUN cd /opt/python && uv sync
ENV PATH="/opt/python/.venv/bin:$PATH"
ENV UV_PROJECT_ENVIRONMENT="/opt/python/.venv"
RUN mkdir -p /tmp/uv-cache && chmod -R 777 /tmp/uv-cache

# Install npm packages globally in the container
COPY package.json package-lock.json /opt/node/
RUN cd /opt/node && \
  npm ci && \
  rm /opt/node/package.json /opt/node/package-lock.json
ENV NODE_PATH="/opt/node/node_modules"
ENV PATH="/opt/node/node_modules/.bin:$PATH"
ENV IN_UDB_CONTAINER=true

# install gems
ENV BUNDLE_PATH=/usr/local/bundle
ENV BUNDLE_BIN=/usr/local/bundle/bin
ENV GEM_HOME=/usr/local/bundle
ENV GEM_PATH=/usr/local/bundle
ENV PATH="/usr/local/bundle/bin:$PATH"

# Create the bundle directory
RUN mkdir -p /usr/local/bundle \
    && chmod 1777 /usr/local/bundle

COPY Gemfile /opt/Gemfile
COPY Gemfile.lock /opt/Gemfile.lock
COPY tools/ruby-gems/idlc/idlc.gemspec /opt/tools/ruby-gems/idlc/
COPY tools/ruby-gems/idlc/lib/gem_versions.rb /opt/tools/ruby-gems/idlc/lib/
COPY tools/ruby-gems/idlc/lib/idlc/version.rb /opt/tools/ruby-gems/idlc/lib/idlc/
COPY tools/ruby-gems/idl_highlighter/idl_highlighter.gemspec /opt/tools/ruby-gems/idl_highlighter/
COPY tools/ruby-gems/idl_highlighter/lib/idl_highlighter/version.rb /opt/tools/ruby-gems/idl_highlighter/lib/idl_highlighter/
COPY tools/ruby-gems/udb/udb.gemspec /opt/tools/ruby-gems/udb/
COPY tools/ruby-gems/udb/lib/gem_versions.rb /opt/tools/ruby-gems/udb/lib/
COPY tools/ruby-gems/udb/lib/udb/version.rb /opt/tools/ruby-gems/udb/lib/udb/
COPY tools/ruby-gems/udb-gen/udb-gen.gemspec /opt/tools/ruby-gems/udb-gen/
COPY tools/ruby-gems/udb-gen/lib/gem_versions.rb /opt/tools/ruby-gems/udb-gen/lib/
COPY tools/ruby-gems/udb-gen/lib/udb-gen/version.rb /opt/tools/ruby-gems/udb-gen/lib/udb-gen/
COPY tools/ruby-gems/udb_helpers/udb_helpers.gemspec /opt/tools/ruby-gems/udb_helpers/
COPY tools/ruby-gems/udb_helpers/lib/udb_helpers/version.rb /opt/tools/ruby-gems/udb_helpers/lib/udb_helpers/
RUN bundle install --gemfile /opt/Gemfile --jobs $(nproc) \
    && chmod -R a+rwX /usr/local/bundle

# the binaries for gems need to be copied in
RUN mkdir -p /workspace/bin/container
COPY tools/ruby-gems/idlc/bin/idlc /workspace/bin/container
COPY tools/ruby-gems/udb/bin/udb /workspace/bin/container
COPY tools/ruby-gems/udb-gen/bin/udb-gen /workspace/bin/container
ENV PATH="/workspace/bin/container:$PATH"

# Grant the default ubuntu user sudo access
RUN echo ubuntu ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/ubuntu \
    && chmod 0440 /etc/sudoers.d/ubuntu
