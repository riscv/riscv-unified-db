// Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
// SPDX-License-Identifier: BSD-3-Clause-Clear

import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

// Load IDL TextMate grammar for Shiki. AUTO-GENERATED from the tree-sitter IDL grammar;
// regenerate with: bin/chore gen idl-highlight
// require() is used because @shikijs/rehype is a pure ESM package loaded below
// via dynamic import(), and mixing static imports with it causes module-type issues.
// eslint-disable-next-line @typescript-eslint/no-require-imports
const idlLang = require('../tools/vscode/idl/syntaxes/idl.tmLanguage.json');
// Shiki's language name is matched against fenced code block language tags.
// The tmLanguage has name "IDL" (uppercase); add a lowercase alias so that
// ```idl fences work without needing to write ```IDL.
idlLang.aliases = ['idl'];

export default async function createConfig(): Promise<Config> {
  // Dynamic import is required because @shikijs/rehype is a pure ESM package.
  const { default: rehypeShiki } = await import('@shikijs/rehype');

  return {
    title: 'UDB — RISC-V Unified Database',
    tagline: 'The single source of truth for the RISC-V specification',
    favicon: 'img/udb-block.svg',

    future: {
      v4: true,
    },

    url: process.env.DOCUSAURUS_URL ?? 'https://riscv.github.io',
    baseUrl: process.env.DOCUSAURUS_BASE_URL ?? '/riscv-unified-db/docs-preview/',

    organizationName: 'riscv',
    projectName: 'riscv-unified-db',

    // TODO: change back to 'throw' once content pages exist (Phase 13+)
    onBrokenLinks: 'warn',

    markdown: {
      hooks: {
        onBrokenMarkdownLinks: 'warn',
      },
    },

    i18n: {
      defaultLocale: 'en',
      locales: ['en'],
    },

    presets: [
      [
        'classic',
        {
          docs: {
            sidebarPath: './sidebars.ts',
            editUrl: 'https://github.com/riscv/riscv-unified-db/tree/main/doc/',
            exclude: ['planning/**'],
            showLastUpdateTime: true,
            // Shiki processes fenced code blocks at the rehype level.
            // defaultColor:false emits CSS vars; custom.css activates light/dark.
            rehypePlugins: [
              [rehypeShiki, {
                themes: {
                  light: 'github-light',
                  dark:  'dracula',
                },
                langs: [idlLang],
                langAlias: {idl: 'IDL'},
                defaultColor: false,
              }],
            ],
          },
          blog: false,
          theme: {
            customCss: './src/css/custom.css',
          },
        } satisfies Preset.Options,
      ],
    ],

    themeConfig: {
      image: 'img/udb-social-card.jpg',
      announcementBar: {
        id: 'under_construction',
        content: '🚧 This documentation site is under active construction. See <a href="docs/intro/doc-status">Documentation Status</a> for details.',
        backgroundColor: '#ffa500',
        textColor: '#000000',
        isCloseable: true,
      },
      colorMode: {
        respectPrefersColorScheme: true,
      },
      navbar: {
        title: 'UDB',
        logo: {
          alt: 'UDB Logo',
          src: 'img/udb.svg',
        },
        items: [
          {
            type: 'dropdown',
            label: 'Getting Started',
            position: 'left',
            items: [
              {label: 'For Users', to: '/docs/getting-started/users'},
              {label: 'For Spec Writers', to: '/docs/getting-started/spec-writers'},
              {label: 'For Developers', to: '/docs/getting-started/developers'},
            ],
          },
          {
            type: 'dropdown',
            label: 'Documentation',
            position: 'left',
            items: [
              {label: 'Introduction', to: '/docs/intro/what-is-udb'},
              {label: 'Schema Reference', to: '/docs/schemas'},
              {label: 'Configurations', to: '/docs/concepts/configurations/overview'},
              {label: 'Tools', to: '/docs/tools/overview'},
              {label: 'Generators', to: '/docs/generators/overview'},
            ],
          },
          {
            label: 'IDL',
            to: '/docs/idl',
            position: 'left',
          },
          {
            label: 'API Reference',
            to: '/api',
            position: 'left',
          },
          {
            label: 'Contributing',
            to: '/docs/contributing',
            position: 'left',
          },
          {
            label: 'Browse Spec',
            href: 'https://riscv.github.io/riscv-unified-db/',
            position: 'right',
          },
          {
            label: 'GitHub',
            href: 'https://github.com/riscv/riscv-unified-db',
            position: 'right',
          },
        ],
      },
      footer: {
        style: 'dark',
        links: [
          {
            title: 'Docs',
            items: [
              {label: 'Getting Started', to: '/docs/getting-started/users'},
              {label: 'IDL Language', to: '/docs/idl/overview'},
              {label: 'Contributing', to: '/docs/contributing'},
            ],
          },
          {
            title: 'Project',
            items: [
              {
                label: 'GitHub',
                href: 'https://github.com/riscv/riscv-unified-db',
              },
              {
                label: 'Issues',
                href: 'https://github.com/riscv/riscv-unified-db/issues',
              },
            ],
          },
        ],
        copyright: `Copyright © ${new Date().getFullYear()} RISC-V International. Licensed under BSD-3-Clause-Clear. Built with Docusaurus.`,
      },
      // Prism is kept for inline code and any explicit <CodeBlock> JSX components.
      // Fenced code blocks in markdown are handled by Shiki (see markdown.rehypePlugins).
      prism: {
        theme: prismThemes.github,
        darkTheme: prismThemes.dracula,
        additionalLanguages: ['yaml', 'json', 'bash'],
      },
    } satisfies Preset.ThemeConfig,
  };
}
