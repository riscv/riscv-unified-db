// Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
// SPDX-License-Identifier: BSD-3-Clause-Clear

import siteConfig from '@generated/docusaurus.config';

export default function prismIncludeLanguages(PrismObject) {
  const {
    themeConfig: {prism},
  } = siteConfig;
  const {additionalLanguages} = prism;

  additionalLanguages.forEach((lang) => {
    require(`prismjs/components/prism-${lang}`);
  });

  // Load IDL language definition (canonical source: doc/src/prism/idl.js)
  require('@site/src/prism/idl')(PrismObject);
}
