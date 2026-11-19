# UDB and spec, no Sail (`0b011`)

Parameters: **42**

## `FORCE_UPGRADE_CBO_INVAL_TO_FLUSH`

- **Class:** `0b011`
- **UDB YAML:** `spec/std/isa/param/FORCE_UPGRADE_CBO_INVAL_TO_FLUSH.yaml`
- **Sail near-match, rejected:** `base.reserved_behavior.xenvcfg_cbie` handles reserved `xenvcfg.CBIE=0b10` writes; it does not represent whether `CBIE=0b11` permits invalidate or forces flush (`model/core/platform_config.sail:283-287,313`; `model/core/sys_regs.sail:496-502`; `config/config.json.in:238-242`).
- **Spec evidence/anchor:** src/priv/machine.adoc:2252 [norm:menvcfg_cbie_cbo-inval_op_lead-in]
## `HSTATEEN_AIA_TYPE`

- **Class:** `0b011`
- **UDB YAML:** `spec/std/isa/param/HSTATEEN_AIA_TYPE.yaml`
- **Sail match/evidence:** —
- **Spec evidence/anchor:** src/priv/smstateen.adoc:296 [norm:hstateen0_aia_op]
## `HSTATEEN_IMSIC_TYPE`

- **Class:** `0b011`
- **UDB YAML:** `spec/std/isa/param/HSTATEEN_IMSIC_TYPE.yaml`
- **Sail match/evidence:** —
- **Spec evidence/anchor:** src/priv/smstateen.adoc:284 [norm:hstateen0_imsic_op]
## `HSTATEEN_JVT_TYPE`

- **Class:** `0b011`
- **UDB YAML:** `spec/std/isa/param/HSTATEEN_JVT_TYPE.yaml`
- **Sail match/evidence:** —
- **Spec evidence/anchor:** src/priv/smstateen.adoc:263 [norm:stateen0_jvt_op]
## `IMPRECISE_VECTOR_TRAP_SETTABLE`

- **Class:** `0b011`
- **UDB YAML:** `spec/std/isa/param/IMPRECISE_VECTOR_TRAP_SETTABLE.yaml`
- **Sail match/evidence:** —
- **Spec evidence/anchor:** src/unpriv/vector-common.adoc:5001 [selectable precise/imprecise vector traps]
## `JVT_BASE_MASK`

- **Class:** `0b011`
- **UDB YAML:** `spec/std/isa/param/JVT_BASE_MASK.yaml`
- **Sail match/evidence:** —
- **Spec evidence/anchor:** src/unpriv/zcmt.adoc:122 [norm:jvt_op]
## `JVT_BASE_TYPE`

- **Class:** `0b011`
- **UDB YAML:** `spec/std/isa/param/JVT_BASE_TYPE.yaml`
- **Sail match/evidence:** —
- **Spec evidence/anchor:** src/unpriv/zcmt.adoc:122 [norm:jvt_op]
## `JVT_READ_ONLY`

- **Class:** `0b011`
- **UDB YAML:** `spec/std/isa/param/JVT_READ_ONLY.yaml`
- **Sail match/evidence:** —
- **Spec evidence/anchor:** src/unpriv/zcmt.adoc:122 [norm:jvt_op]
## `LRSC_FAIL_ON_VA_SYNONYM`

- **Class:** `0b011`
- **UDB YAML:** `spec/std/isa/param/LRSC_FAIL_ON_VA_SYNONYM.yaml`
- **Sail match/evidence:** —
- **Spec evidence/anchor:** src/unpriv/zalrsc.adoc:204 [norm:lrsc_same_address_and_size]
## `MCTRCTL_CORSWAPINH_IMPLEMENTED`

- **Class:** `0b011`
- **UDB YAML:** `spec/std/isa/param/MCTRCTL_CORSWAPINH_IMPLEMENTED.yaml`
- **Sail match/evidence:** —
- **Spec evidence/anchor:** src/priv/smctr.adoc:97 [norm:mctrctl_corswapinh_op]
## `MCTRCTL_CUSTOM_IMPLEMENTED`

- **Class:** `0b011`
- **UDB YAML:** `spec/std/isa/param/MCTRCTL_CUSTOM_IMPLEMENTED.yaml`
- **Sail match/evidence:** —
- **Spec evidence/anchor:** src/priv/smctr.adoc:104 [norm:mctrctl_custom_op]
## `MCTRCTL_DIRCALLINH_IMPLEMENTED`

- **Class:** `0b011`
- **UDB YAML:** `spec/std/isa/param/MCTRCTL_DIRCALLINH_IMPLEMENTED.yaml`
- **Sail match/evidence:** —
- **Spec evidence/anchor:** src/priv/smctr.adoc:91 [norm:mctrctl_dircallinh_op]
## `MCTRCTL_DIRJMPINH_IMPLEMENTED`

- **Class:** `0b011`
- **UDB YAML:** `spec/std/isa/param/MCTRCTL_DIRJMPINH_IMPLEMENTED.yaml`
- **Sail match/evidence:** —
- **Spec evidence/anchor:** src/priv/smctr.adoc:95 [norm:mctrctl_dirjmpinh_op]
## `MCTRCTL_DIRLJMPINH_IMPLEMENTED`

- **Class:** `0b011`
- **UDB YAML:** `spec/std/isa/param/MCTRCTL_DIRLJMPINH_IMPLEMENTED.yaml`
- **Sail match/evidence:** —
- **Spec evidence/anchor:** src/priv/smctr.adoc:103 [norm:mctrctl_dirljmpinh_op]
## `MCTRCTL_EXCINH_IMPLEMENTED`

- **Class:** `0b011`
- **UDB YAML:** `spec/std/isa/param/MCTRCTL_EXCINH_IMPLEMENTED.yaml`
- **Sail match/evidence:** —
- **Spec evidence/anchor:** src/priv/smctr.adoc:79 [norm:mctrctl_excinh_op]
## `MCTRCTL_INDCALLINH_IMPLEMENTED`

- **Class:** `0b011`
- **UDB YAML:** `spec/std/isa/param/MCTRCTL_INDCALLINH_IMPLEMENTED.yaml`
- **Sail match/evidence:** —
- **Spec evidence/anchor:** src/priv/smctr.adoc:89 [norm:mctrctl_indcallinh_op]
## `MCTRCTL_INDJMPINH_IMPLEMENTED`

- **Class:** `0b011`
- **UDB YAML:** `spec/std/isa/param/MCTRCTL_INDJMPINH_IMPLEMENTED.yaml`
- **Sail match/evidence:** —
- **Spec evidence/anchor:** src/priv/smctr.adoc:93 [norm:mctrctl_indjmpinh_op]
## `MCTRCTL_INDLJMPINH_IMPLEMENTED`

- **Class:** `0b011`
- **UDB YAML:** `spec/std/isa/param/MCTRCTL_INDLJMPINH_IMPLEMENTED.yaml`
- **Sail match/evidence:** —
- **Spec evidence/anchor:** src/priv/smctr.adoc:101 [norm:mctrctl_indljmpinh_op]
## `MCTRCTL_INTRINH_IMPLEMENTED`

- **Class:** `0b011`
- **UDB YAML:** `spec/std/isa/param/MCTRCTL_INTRINH_IMPLEMENTED.yaml`
- **Sail match/evidence:** —
- **Spec evidence/anchor:** src/priv/smctr.adoc:81 [norm:mctrctl_intrinh_op]
## `MCTRCTL_MTE_IMPLEMENTED`

- **Class:** `0b011`
- **UDB YAML:** `spec/std/isa/param/MCTRCTL_MTE_IMPLEMENTED.yaml`
- **Sail match/evidence:** —
- **Spec evidence/anchor:** src/priv/smctr.adoc:71 [norm:mctrctl_mte_op]
## `MCTRCTL_NTBREN_IMPLEMENTED`

- **Class:** `0b011`
- **UDB YAML:** `spec/std/isa/param/MCTRCTL_NTBREN_IMPLEMENTED.yaml`
- **Sail match/evidence:** —
- **Spec evidence/anchor:** src/priv/smctr.adoc:85 [norm:mctrctl_ntbren_op]
## `MCTRCTL_RASEMU_IMPLEMENTED`

- **Class:** `0b011`
- **UDB YAML:** `spec/std/isa/param/MCTRCTL_RASEMU_IMPLEMENTED.yaml`
- **Sail match/evidence:** —
- **Spec evidence/anchor:** src/priv/smctr.adoc:69 [norm:mctrctl_rasemu_op]
## `MCTRCTL_RETINH_IMPLEMENTED`

- **Class:** `0b011`
- **UDB YAML:** `spec/std/isa/param/MCTRCTL_RETINH_IMPLEMENTED.yaml`
- **Sail match/evidence:** —
- **Spec evidence/anchor:** src/priv/smctr.adoc:99 [norm:mctrctl_retinh_op]
## `MCTRCTL_STE_IMPLEMENTED`

- **Class:** `0b011`
- **UDB YAML:** `spec/std/isa/param/MCTRCTL_STE_IMPLEMENTED.yaml`
- **Sail match/evidence:** —
- **Spec evidence/anchor:** src/priv/smctr.adoc:73 [norm:mctrctl_ste_op]
## `MCTRCTL_TKBRINH_IMPLEMENTED`

- **Class:** `0b011`
- **UDB YAML:** `spec/std/isa/param/MCTRCTL_TKBRINH_IMPLEMENTED.yaml`
- **Sail match/evidence:** —
- **Spec evidence/anchor:** src/priv/smctr.adoc:87 [norm:mctrctl_tkbrinh_op]
## `MCTRCTL_TRETINH_IMPLEMENTED`

- **Class:** `0b011`
- **UDB YAML:** `spec/std/isa/param/MCTRCTL_TRETINH_IMPLEMENTED.yaml`
- **Sail match/evidence:** —
- **Spec evidence/anchor:** src/priv/smctr.adoc:83 [norm:mctrctl_tretinh_op]
## `MSTATEEN_AIA_TYPE`

- **Class:** `0b011`
- **UDB YAML:** `spec/std/isa/param/MSTATEEN_AIA_TYPE.yaml`
- **Sail match/evidence:** —
- **Spec evidence/anchor:** src/priv/smstateen.adoc:294 [norm:mstateen0_aia_op]
## `MSTATEEN_IMSIC_TYPE`

- **Class:** `0b011`
- **UDB YAML:** `spec/std/isa/param/MSTATEEN_IMSIC_TYPE.yaml`
- **Sail match/evidence:** —
- **Spec evidence/anchor:** src/priv/smstateen.adoc:283 [norm:mstateen0_imsic_op]
## `MSTATEEN_JVT_TYPE`

- **Class:** `0b011`
- **UDB YAML:** `spec/std/isa/param/MSTATEEN_JVT_TYPE.yaml`
- **Sail match/evidence:** —
- **Spec evidence/anchor:** src/priv/smstateen.adoc:263 [norm:stateen0_jvt_op]
## `MUTABLE_MISA_Q`

- **Class:** `0b011`
- **UDB YAML:** `spec/std/isa/param/MUTABLE_MISA_Q.yaml`
- **Sail match/evidence:** —
- **Spec evidence/anchor:** src/priv/machine.adoc:73 [norm:misa_extensions_disabling]
## `SCTRDEPTH_DEPTH_LEGAL_VALUES`

- **Class:** `0b011`
- **UDB YAML:** `spec/std/isa/param/SCTRDEPTH_DEPTH_LEGAL_VALUES.yaml`
- **Sail match/evidence:** —
- **Spec evidence/anchor:** src/priv/smctr.adoc:215 [norm:sctrdepth_depth]
## `SSTATEEN_JVT_TYPE`

- **Class:** `0b011`
- **UDB YAML:** `spec/std/isa/param/SSTATEEN_JVT_TYPE.yaml`
- **Sail match/evidence:** —
- **Spec evidence/anchor:** src/priv/smstateen.adoc:263 [norm:stateen0_jvt_op]
## `TINST_VALUE_ON_BREAKPOINT`

- **Class:** `0b011`
- **UDB YAML:** `spec/std/isa/param/TINST_VALUE_ON_BREAKPOINT.yaml`
- **Sail match/evidence:** —
- **Spec evidence/anchor:** src/priv/hypervisor.adoc:2664 [norm:H_trap_xtinst_val]
## `TINST_VALUE_ON_FINAL_INSTRUCTION_GUEST_PAGE_FAULT`

- **Class:** `0b011`
- **UDB YAML:** `spec/std/isa/param/TINST_VALUE_ON_FINAL_INSTRUCTION_GUEST_PAGE_FAULT.yaml`
- **Sail match/evidence:** —
- **Spec evidence/anchor:** src/priv/hypervisor.adoc:2835 [norm:H_trap_xtinst_guestpage]
## `TINST_VALUE_ON_INSTRUCTION_ADDRESS_MISALIGNED`

- **Class:** `0b011`
- **UDB YAML:** `spec/std/isa/param/TINST_VALUE_ON_INSTRUCTION_ADDRESS_MISALIGNED.yaml`
- **Sail match/evidence:** —
- **Spec evidence/anchor:** src/priv/hypervisor.adoc:2664 [norm:H_trap_xtinst_val]
## `TINST_VALUE_ON_MCALL`

- **Class:** `0b011`
- **UDB YAML:** `spec/std/isa/param/TINST_VALUE_ON_MCALL.yaml`
- **Sail match/evidence:** —
- **Spec evidence/anchor:** src/priv/hypervisor.adoc:2664 [norm:H_trap_xtinst_val]
## `TINST_VALUE_ON_SCALL`

- **Class:** `0b011`
- **UDB YAML:** `spec/std/isa/param/TINST_VALUE_ON_SCALL.yaml`
- **Sail match/evidence:** —
- **Spec evidence/anchor:** src/priv/hypervisor.adoc:2664 [norm:H_trap_xtinst_val]
## `TINST_VALUE_ON_UCALL`

- **Class:** `0b011`
- **UDB YAML:** `spec/std/isa/param/TINST_VALUE_ON_UCALL.yaml`
- **Sail match/evidence:** —
- **Spec evidence/anchor:** src/priv/hypervisor.adoc:2664 [norm:H_trap_xtinst_val]
## `TINST_VALUE_ON_VIRTUAL_INSTRUCTION`

- **Class:** `0b011`
- **UDB YAML:** `spec/std/isa/param/TINST_VALUE_ON_VIRTUAL_INSTRUCTION.yaml`
- **Sail match/evidence:** —
- **Spec evidence/anchor:** src/priv/hypervisor.adoc:2664 [norm:H_trap_xtinst_val]
## `TINST_VALUE_ON_VSCALL`

- **Class:** `0b011`
- **UDB YAML:** `spec/std/isa/param/TINST_VALUE_ON_VSCALL.yaml`
- **Sail match/evidence:** —
- **Spec evidence/anchor:** src/priv/hypervisor.adoc:2664 [norm:H_trap_xtinst_val]
## `U_MODE_ENDIANNESS`

- **Class:** `0b011`
- **UDB YAML:** `spec/std/isa/param/U_MODE_ENDIANNESS.yaml`
- **Sail match/evidence:** —
- **Spec evidence/anchor:** src/priv/machine.adoc:654 [norm:mstatus_ube_op]
## `VU_MODE_ENDIANNESS`

- **Class:** `0b011`
- **UDB YAML:** `spec/std/isa/param/VU_MODE_ENDIANNESS.yaml`
- **Sail match/evidence:** —
- **Spec evidence/anchor:** src/priv/hypervisor.adoc:1223 [norm:vsstatus_ube]
