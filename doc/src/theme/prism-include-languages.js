// Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
// SPDX-License-Identifier: BSD-3-Clause-Clear

import siteConfig from '@generated/docusaurus.config';

export default function prismIncludeLanguages(PrismObject) {
  const {
    themeConfig: {prism},
  } = siteConfig;
  const {additionalLanguages} = prism;

  // Set up global Prism BEFORE loading any components
  globalThis.Prism = PrismObject;
  if (typeof window !== 'undefined') {
    window.Prism = PrismObject;
  }

  // Now dynamically import and load YAML
  additionalLanguages.forEach((lang) => {
    try {
      const langModule = require(`prismjs/components/prism-${lang}`);
      // If the module exports a function, call it with PrismObject
      if (typeof langModule === 'function') {
        langModule(PrismObject);
      }
    } catch (e) {
      console.error(`Failed to load Prism language: ${lang}`, e);
    }
  });

  // Load IDL language definition (canonical source: doc/src/prism/idl.js)
  require('@site/src/prism/idl')(PrismObject);
}
