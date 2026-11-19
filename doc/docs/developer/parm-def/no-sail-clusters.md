# Future-development clusters: UDB without Sail

These clusters reorganize the **42 existing entries** in [no-sail.md](no-sail.md) (0b011) for human review. Class membership and parameter data are unchanged. The source class report remains authoritative for per-entry evidence and uncertainty.

Absence from UDB or Sail is a candidate for investigation, not proof of a defect. Check surrounding extension/model coverage and intended scope before proposing changes. Cluster confidence describes thematic coherence, not proof that implementation work is required.

**Coverage:** 42 entries in 9 primary clusters; every class entry appears exactly once.

## 1. CBO invalidate-versus-flush policy (1)

**Commonality:** This parameter distinguishes whether CBIE=0b11 permits invalidate or upgrades it to flush. The class report rejects xenvcfg_cbie as a near-match because it covers reserved CBIE=0b10 writes.

**Possible next investigation:** If Sail should expose this policy, model CBIE=0b11 explicitly; do not reuse the reserved-value setting without semantic proof.

**Confidence and caveat:** High confidence in the distinction; whether Sail should expose the policy needs review.

**Members:**

- [FORCE_UPGRADE_CBO_INVAL_TO_FLUSH](no-sail.md#force_upgrade_cbo_inval_to_flush)

## 2. State-enable register feature/type controls (7)

**Commonality:** AIA, IMSIC, and JVT type parameters occur at machine, supervisor, and hypervisor Stateen levels.

**Possible next investigation:** Review Stateen CSR semantics and add controls only where specification and model require distinct behavior.

**Confidence and caveat:** High thematic coherence; check per-level applicability.

**Members:**

- [HSTATEEN_AIA_TYPE](no-sail.md#hstateen_aia_type)
- [HSTATEEN_IMSIC_TYPE](no-sail.md#hstateen_imsic_type)
- [HSTATEEN_JVT_TYPE](no-sail.md#hstateen_jvt_type)
- [MSTATEEN_AIA_TYPE](no-sail.md#mstateen_aia_type)
- [MSTATEEN_IMSIC_TYPE](no-sail.md#mstateen_imsic_type)
- [MSTATEEN_JVT_TYPE](no-sail.md#mstateen_jvt_type)
- [SSTATEEN_JVT_TYPE](no-sail.md#sstateen_jvt_type)

## 3. Jump Vector Table configuration (3)

**Commonality:** Base mask, base type, and read-only policy all describe JVT configuration.

**Possible next investigation:** Check whether Sail's Zcmt/JVT model should expose these properties while preserving spec constraints.

**Confidence and caveat:** High thematic coherence; verify current Sail support.

**Members:**

- [JVT_BASE_MASK](no-sail.md#jvt_base_mask)
- [JVT_BASE_TYPE](no-sail.md#jvt_base_type)
- [JVT_READ_ONLY](no-sail.md#jvt_read_only)

## 4. Control-transfer recording controls and depth (18)

**Commonality:** MCTRCTL feature/inhibit bits and SCTRDEPTH legal values concern the control-transfer-recording facility.

**Possible next investigation:** Review Sail CTR state and event/filter behavior; decide whether controls and depth are parameters or intentionally fixed.

**Confidence and caveat:** High thematic coherence; confirm common configuration boundary.

**Members:**

- [MCTRCTL_CORSWAPINH_IMPLEMENTED](no-sail.md#mctrctl_corswapinh_implemented)
- [MCTRCTL_CUSTOM_IMPLEMENTED](no-sail.md#mctrctl_custom_implemented)
- [MCTRCTL_DIRCALLINH_IMPLEMENTED](no-sail.md#mctrctl_dircallinh_implemented)
- [MCTRCTL_DIRJMPINH_IMPLEMENTED](no-sail.md#mctrctl_dirjmpinh_implemented)
- [MCTRCTL_DIRLJMPINH_IMPLEMENTED](no-sail.md#mctrctl_dirljmpinh_implemented)
- [MCTRCTL_EXCINH_IMPLEMENTED](no-sail.md#mctrctl_excinh_implemented)
- [MCTRCTL_INDCALLINH_IMPLEMENTED](no-sail.md#mctrctl_indcallinh_implemented)
- [MCTRCTL_INDJMPINH_IMPLEMENTED](no-sail.md#mctrctl_indjmpinh_implemented)
- [MCTRCTL_INDLJMPINH_IMPLEMENTED](no-sail.md#mctrctl_indljmpinh_implemented)
- [MCTRCTL_INTRINH_IMPLEMENTED](no-sail.md#mctrctl_intrinh_implemented)
- [MCTRCTL_MTE_IMPLEMENTED](no-sail.md#mctrctl_mte_implemented)
- [MCTRCTL_NTBREN_IMPLEMENTED](no-sail.md#mctrctl_ntbren_implemented)
- [MCTRCTL_RASEMU_IMPLEMENTED](no-sail.md#mctrctl_rasemu_implemented)
- [MCTRCTL_RETINH_IMPLEMENTED](no-sail.md#mctrctl_retinh_implemented)
- [MCTRCTL_STE_IMPLEMENTED](no-sail.md#mctrctl_ste_implemented)
- [MCTRCTL_TKBRINH_IMPLEMENTED](no-sail.md#mctrctl_tkbrinh_implemented)
- [MCTRCTL_TRETINH_IMPLEMENTED](no-sail.md#mctrctl_tretinh_implemented)
- [SCTRDEPTH_DEPTH_LEGAL_VALUES](no-sail.md#sctrdepth_depth_legal_values)

## 5. Transformed-instruction values across trap causes (8)

**Commonality:** TINST_VALUE entries specify transformed instruction values associated with different trap/exception events.

**Possible next investigation:** Compare Sail trap paths per event and decide whether values are fixed behavior or configurable policy.

**Confidence and caveat:** High thematic coherence; check event-specific coverage.

**Members:**

- [TINST_VALUE_ON_BREAKPOINT](no-sail.md#tinst_value_on_breakpoint)
- [TINST_VALUE_ON_FINAL_INSTRUCTION_GUEST_PAGE_FAULT](no-sail.md#tinst_value_on_final_instruction_guest_page_fault)
- [TINST_VALUE_ON_INSTRUCTION_ADDRESS_MISALIGNED](no-sail.md#tinst_value_on_instruction_address_misaligned)
- [TINST_VALUE_ON_MCALL](no-sail.md#tinst_value_on_mcall)
- [TINST_VALUE_ON_SCALL](no-sail.md#tinst_value_on_scall)
- [TINST_VALUE_ON_UCALL](no-sail.md#tinst_value_on_ucall)
- [TINST_VALUE_ON_VIRTUAL_INSTRUCTION](no-sail.md#tinst_value_on_virtual_instruction)
- [TINST_VALUE_ON_VSCALL](no-sail.md#tinst_value_on_vscall)

## 6. User and virtual-user endianness (2)

**Commonality:** The two settings distinguish U-mode and VU-mode endianness.

**Possible next investigation:** Check whether Sail access endianness is independently configurable for these contexts and preserves virtualization semantics.

**Confidence and caveat:** High thematic coherence; verify model assumptions.

**Members:**

- [U_MODE_ENDIANNESS](no-sail.md#u_mode_endianness)
- [VU_MODE_ENDIANNESS](no-sail.md#vu_mode_endianness)

## 7. Vector trap precision policy (1)

**Commonality:** The parameter controls whether vector traps are selectable as precise or imprecise.

**Possible next investigation:** Inspect Sail vector exception/trap behavior and determine whether this is configurable or fixed.

**Confidence and caveat:** Medium; singleton retained for a focused question.

**Members:**

- [IMPRECISE_VECTOR_TRAP_SETTABLE](no-sail.md#imprecise_vector_trap_settable)

## 8. LR/SC virtual-address synonym behavior (1)

**Commonality:** The parameter asks whether LR/SC can fail when virtual synonyms refer to one physical location.

**Possible next investigation:** Review Sail reservation/address-translation behavior against the linked Zalrsc rule.

**Confidence and caveat:** Medium; singleton retained for focused triage.

**Members:**

- [LRSC_FAIL_ON_VA_SYNONYM](no-sail.md#lrsc_fail_on_va_synonym)

## 9. Mutability of the MISA Q-extension bit (1)

**Commonality:** The parameter concerns whether the Q bit in MISA can change at runtime.

**Possible next investigation:** Check Sail MISA write semantics and determine whether mutability is supported, fixed, or out of scope.

**Confidence and caveat:** Medium; singleton retained for focused triage.

**Members:**

- [MUTABLE_MISA_Q](no-sail.md#mutable_misa_q)
