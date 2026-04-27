// Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
// SPDX-License-Identifier: BSD-3-Clause-Clear

import React from 'react';
import styles from './styles.module.css';

// Import IDL logo variants as React components
import IdlAppIcon from '@site/static/img/idl-app-icon.svg';
import IdlNavbarLogo from '@site/static/img/idl-navbar-logo.svg';

export interface IDLPageHeaderProps {
  /** Variant: 'compact' for small icon, 'wide' for horizontal lockup with text */
  variant?: 'compact' | 'wide';
  /** Subtitle text to display next to the logo */
  subtitle?: string;
  /** Additional CSS class name */
  className?: string;
}

/**
 * IDL Page Header component
 *
 * Displays the IDL logo with optional subtitle.
 * - Use 'wide' variant on overview pages (includes "ISA Description Language" text)
 * - Use 'compact' variant on reference pages (icon only)
 */
export default function IDLPageHeader({
  variant = 'compact',
  subtitle,
  className,
}: IDLPageHeaderProps): React.JSX.Element {
  const Logo = variant === 'wide' ? IdlNavbarLogo : IdlAppIcon;

  return (
    <div className={`${styles.idlPageHeader} ${className || ''}`}>
      <Logo
        className={styles.idlLogo}
        style={{
          height: variant === 'wide' ? '60px' : '48px',
          width: 'auto',
        }}
        title="IDL - ISA Description Language"
      />
      {subtitle && <span className={styles.subtitle}>{subtitle}</span>}
    </div>
  );
}
