// Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
// SPDX-License-Identifier: BSD-3-Clause-Clear

import React from 'react';
import Link from '@docusaurus/Link';
import useBaseUrl from '@docusaurus/useBaseUrl';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import {useThemeConfig} from '@docusaurus/theme-common';
import ThemedImage from '@theme/ThemedImage';

// Import the SVG as a React component so CSS variables work
import UdbLogoSvg from '@site/static/img/udb-navbar.svg';

export default function Logo(props: {imageClassName?: string; titleClassName?: string}): React.JSX.Element {
  const {
    siteConfig: {title},
  } = useDocusaurusContext();
  const {
    navbar: {title: navbarTitle, logo},
  } = useThemeConfig();

  const logoLink = useBaseUrl(logo?.href || '/');
  const sources = {
    light: useBaseUrl(logo?.src || ''),
    dark: useBaseUrl(logo?.srcDark || logo?.src || ''),
  };

  return (
    <Link
      to={logoLink}
      {...props}
      {...(logo?.target && {target: logo.target})}>
      {/* Use the imported SVG component so CSS variables apply */}
      <UdbLogoSvg
        className={props.imageClassName}
        style={{height: '32px', width: 'auto'}}
        title={logo?.alt || title}
      />
      {navbarTitle != null && <b className={props.titleClassName}>{navbarTitle}</b>}
    </Link>
  );
}
