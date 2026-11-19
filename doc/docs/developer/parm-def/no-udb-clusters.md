# Future-development clusters: Sail without UDB

These clusters reorganize the **15 existing entries** in [no-udb.md](no-udb.md) (0b101) for human review. Class membership and parameter data are unchanged. The source class report remains authoritative for per-entry evidence and uncertainty.

Absence from UDB or Sail is a candidate for investigation, not proof of a defect. Check surrounding extension/model coverage and intended scope before proposing changes. Cluster confidence describes thematic coherence, not proof that implementation work is required.

**Coverage:** 15 entries in 4 primary clusters; every class entry appears exactly once.

## 1. Base ISA and architectural control defaults (4)

**Commonality:** The E profile, event width, delegation mask, and writable FIO attributes are base-level settings.

**Possible next investigation:** Check whether UDB already represents these through extension/configuration structures; add parameter records only if its modeling scope calls for them.

**Confidence and caveat:** High thematic coherence; omission status unverified.

**Members:**

- [base.E](no-udb.md#basee)
- [base.hpmevent_width_bits](no-udb.md#basehpmevent_width_bits)
- [base.mideleg.read_only_one_bits](no-udb.md#basemidelegread_only_one_bits)
- [base.writable_fiom](no-udb.md#basewritable_fiom)

## 2. Reserved and constrained behavior policies (7)

**Commonality:** All entries share Sail's base.reserved_behavior hierarchy and describe reserved or constrained writes/encodings.

**Possible next investigation:** Compare exact reserved-value policies with UDB constraints and decide which require explicit parameterization.

**Confidence and caveat:** High thematic coherence; absence alone is not a defect.

**Members:**

- [base.reserved_behavior.amocas_odd_register](no-udb.md#basereserved_behavioramocas_odd_register)
- [base.reserved_behavior.fcsr_rm](no-udb.md#basereserved_behaviorfcsr_rm)
- [base.reserved_behavior.pmpcfg_write_only](no-udb.md#basereserved_behaviorpmpcfg_write_only)
- [base.reserved_behavior.rv32zdinx_odd_register](no-udb.md#basereserved_behaviorrv32zdinx_odd_register)
- [base.reserved_behavior.xenvcfg_cbie](no-udb.md#basereserved_behaviorxenvcfg_cbie)
- [base.reserved_behavior.xtvec_mode](no-udb.md#basereserved_behaviorxtvec_mode)
- [base.reserved_behavior.illegal_privilege](no-udb.md#basereserved_behaviorillegal_privilege)

## 3. Platform and hart integration (3)

**Commonality:** Clock frequency, hart identity, and WFI behavior are platform-facing settings.

**Possible next investigation:** Separate architectural contracts from emulator/platform choices; keep platform-only items out of UDB if intentionally out of scope.

**Confidence and caveat:** High thematic coherence; scope needs human review.

**Members:**

- [platform.clock_frequency](no-udb.md#platformclock_frequency)
- [platform.hartid](no-udb.md#platformhartid)
- [platform.wfi_is_nop](no-udb.md#platformwfi_is_nop)

## 4. Vector profile and vector extensions (1)

**Commonality:** `extensions.V.support_level` selects the Sail model's vector capability profile; the corresponding UDB extension-presence declarations are now represented separately.

**Possible next investigation:** Compare Sail's support-level enum with UDB's vector profile/configuration model and decide whether profile detail belongs in UDB parameters.

**Confidence and caveat:** Moderate; this is one configuration leaf, and its absence may be intentional scope rather than a coverage gap.

**Members:**

- [extensions.V.support_level](no-udb.md#extensionsvsupport_level)
