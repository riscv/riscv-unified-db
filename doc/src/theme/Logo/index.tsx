// Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
// SPDX-License-Identifier: BSD-3-Clause-Clear

import React from 'react';
import Link from '@docusaurus/Link';
import useBaseUrl from '@docusaurus/useBaseUrl';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import {useThemeConfig} from '@docusaurus/theme-common';

// Import the SVG as a React component so CSS variables work
import UdbLogoSvg from '@site/static/img/udb-navbar.svg';

type LogoProps = {
  imageClassName?: string;
  titleClassName?: string;
} & React.ComponentProps<typeof Link>;

export default function Logo({imageClassName, titleClassName, ...rest}: LogoProps): React.JSX.Element {
  const {
    siteConfig: {title},
  } = useDocusaurusContext();
  const {
    navbar: {title: navbarTitle, logo},
  } = useThemeConfig();

  const logoLink = useBaseUrl(logo?.href || '/');

  return (
    <Link
      to={logoLink}
      {...rest}
      {...(logo?.target && {target: logo.target})}>
      {/* Use the imported SVG component so CSS variables apply */}
      <UdbLogoSvg
        className={imageClassName}
        style={{height: '32px', width: 'auto'}}
        title={logo?.alt || title}
      />
      {navbarTitle != null && <b className={titleClassName}>{navbarTitle}</b>}
    </Link>
  );
}
