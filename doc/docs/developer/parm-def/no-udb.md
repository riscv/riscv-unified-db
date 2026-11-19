# Spec and Sail, no UDB (`0b101`)
Reverse sweep entries: **120**.

## `base.E`
- **Class:** `0b101`
- **Sail identity:** `base.E`; hierarchy level `base`
- **Schema:** `/properties/base/properties/E`; type `boolean`; definition `{"type":"boolean"}`
- **Sail source evidence:** `model/core/types.sail:24`
- **Spec mention / defining-location candidate:** `src/priv/machine.adoc:67` (E-extension rule). Normative anchor: `norm:misa_e_op`.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** No unique semantic UDB YAML match established; this is a Sail-only record.
## `base.hpmevent_width_bits`
- **Class:** `0b101`
- **Sail identity:** `base.hpmevent_width_bits`; hierarchy level `base`
- **Schema:** `/properties/base/properties/hpmevent_width_bits`; type `integer`; definition `{"maximum":64,"minimum":1,"type":"integer"}`
- **Sail source evidence:** `model/core/platform_config.sail:162`
- **Spec mention / defining-location candidate:** `src/priv/machine.adoc:1534` (architectural concept evidence). Normative anchor: `norm:mhpmevent_sz_warl_op`.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** No unique semantic UDB YAML match established; this is a Sail-only record.
- **Near-match review:** HPM_EVENTS and HPM_COUNTER<n>_WIDTH are different settings (selected event values and counter width).
## `base.mideleg.read_only_one_bits`
- **Class:** `0b101`
- **Sail identity:** `base.mideleg.read_only_one_bits`; hierarchy level `base.mideleg`
- **Schema:** `/properties/base/properties/mideleg/properties/read_only_one_bits`; type `object`; definition `{"allOf":[{"additionalProperties":false,"description":"core/platform_config.sail:40.49-40.87","properties":{"len":{"const":"xlen","type":"string"},"value":{"oneOf":[{"pattern":"^0x[0-9a-fA-F_]+$","type":"string"},{"pattern":"^0b[0-1_]+$","type":"string"},{"pattern":"^[0-9_]+$","type":"string"}]}},"required":["len","value"],"type":"object"},{"additionalProperties":false,"description":"postlude/validate_config.sail:1091.40-1091.78","properties":{"len":{"const":"xlen","type":"string"},"value":{"oneOf":[{"pattern":"^0x[0-9a-fA-F_]+$","type":"string"},{"pattern":"^0b[0-1_]+$","type":"string"},{"pattern":"^[0-9_]+$","type":"string"}]}},"required":["len","value"],"type":"object"}]}`
- **Sail source evidence:** `model/core/platform_config.sail:40-40`, `model/postlude/validate_config.sail:1091-1091`
- **Spec mention / defining-location candidate:** `src/priv/machine.adoc:1271` (architectural concept evidence). Normative anchor: `norm:mideleg_no_rd1`.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** No unique semantic UDB YAML match established; this is a Sail-only record.
- **Near-match review:** MIDELEG_DELEGATABLE is different: delegatable interrupt selection is not the read-only-one WARL policy.
## `base.reserved_behavior.amocas_odd_register`
- **Class:** `0b101`
- **Sail identity:** `base.reserved_behavior.amocas_odd_register`; hierarchy level `base.reserved_behavior`
- **Schema:** `/properties/base/properties/reserved_behavior/properties/amocas_odd_register`; type `string`; definition `{"description":"core/platform_config.sail:306.80-306.129","enum":["AMOCAS_Fatal","AMOCAS_Illegal"],"type":"string"}`
- **Sail source evidence:** `model/core/platform_config.sail:306-306`
- **Spec mention / defining-location candidate:** `src/unpriv/zacas.adoc:48` (architectural concept evidence). Normative anchor: `norm:Zacas_rv32_amocas-d_frst_pair_entry_reg_even`.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** No unique semantic UDB YAML match established; this is a Sail-only record.
## `base.reserved_behavior.fcsr_rm`
- **Class:** `0b101`
- **Sail identity:** `base.reserved_behavior.fcsr_rm`; hierarchy level `base.reserved_behavior`
- **Schema:** `/properties/base/properties/reserved_behavior/properties/fcsr_rm`; type `string`; definition `{"description":"core/platform_config.sail:307.57-307.94","enum":["Fcsr_RM_Fatal","Fcsr_RM_Illegal"],"type":"string"}`
- **Sail source evidence:** `model/core/platform_config.sail:307-307`
- **Spec mention / defining-location candidate:** `src/unpriv/f-st-ext.adoc:71` (architectural concept evidence). Normative anchor: `norm:roundingmode_rsv`.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** No unique semantic UDB YAML match established; this is a Sail-only record.
## `base.reserved_behavior.illegal_privilege`
- **Class:** `0b101`
- **Sail identity:** `base.reserved_behavior.illegal_privilege`; hierarchy level `base.reserved_behavior`
- **Schema:** `/properties/base/properties/reserved_behavior/properties/illegal_privilege`; enum `IllegalPriv_Ignore`, `IllegalPriv_Lowest`
- **Sail source evidence:** `model/core/platform_config.sail:321.77-321.124`; policy applied in `model/core/sys_regs.sail:209`.
- **Spec mention / defining-location candidate:** `src/priv/machine.adoc:392-393` (`norm:mstatus_xpp_enc`) defines legal xPP encodings.
- **Anchor status:** No normative rule found that selects the model's ignore-versus-lowest policy for illegal encodings.
- **UDB match:** None established.
## `base.reserved_behavior.pmpcfg_write_only`
- **Class:** `0b101`
- **Sail identity:** `base.reserved_behavior.pmpcfg_write_only`; hierarchy level `base.reserved_behavior`
- **Schema:** `/properties/base/properties/reserved_behavior/properties/pmpcfg_write_only`; type `string`; definition `{"description":"core/platform_config.sail:308.70-308.117","enum":["PMP_ClearPermissions","PMP_Fatal","PMP_Ignore"],"type":"string"}`
- **Sail source evidence:** `model/core/platform_config.sail:308-308`
- **Spec mention / defining-location candidate:** `src/priv/machine.adoc:3406` (architectural concept evidence); no normative anchor confidently identified.
- **Defining status:** Spec mention found; first defining location remains unresolved.
- **UDB match:** No unique semantic UDB YAML match established; this is a Sail-only record.
## `base.reserved_behavior.rv32zdinx_odd_register`
- **Class:** `0b101`
- **Sail identity:** `base.reserved_behavior.rv32zdinx_odd_register`; hierarchy level `base.reserved_behavior`
- **Schema:** `/properties/base/properties/reserved_behavior/properties/rv32zdinx_odd_register`; type `string`; definition `{"description":"core/platform_config.sail:311.86-311.138","enum":["Zdinx_Fatal","Zdinx_Illegal"],"type":"string"}`
- **Sail source evidence:** `model/core/platform_config.sail:311-311`
- **Spec mention / defining-location candidate:** `src/unpriv/zfinx.adoc:92` (architectural concept evidence). Normative anchor: `norm:Zdinx_x_reg_pair`.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** No unique semantic UDB YAML match established; this is a Sail-only record.
## `base.reserved_behavior.xenvcfg_cbie`
- **Class:** `0b101`
- **Sail identity:** `base.reserved_behavior.xenvcfg_cbie`; hierarchy level `base.reserved_behavior`
- **Schema:** `/properties/base/properties/reserved_behavior/properties/xenvcfg_cbie`; type `string`; definition `{"description":"core/platform_config.sail:309.67-309.109","enum":["Xenvcfg_ClearPermissions","Xenvcfg_Fatal","Xenvcfg_Ignore"],"type":"string"}`
- **Sail source evidence:** `model/core/platform_config.sail:309-309`
- **Spec mention / defining-location candidate:** `src/priv/hypervisor.adoc:686` (architectural concept evidence). Normative anchor: `norm:henvcfg_cbie`.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** No unique semantic UDB YAML match established; this is a Sail-only record.
## `base.reserved_behavior.xtvec_mode`
- **Class:** `0b101`
- **Sail identity:** `base.reserved_behavior.xtvec_mode`; hierarchy level `base.reserved_behavior`
- **Schema:** `/properties/base/properties/reserved_behavior/properties/xtvec_mode`; type `string`; definition `{"description":"core/platform_config.sail:310.63-310.103","enum":["Xtvec_Fatal","Xtvec_Ignore"],"type":"string"}`
- **Sail source evidence:** `model/core/platform_config.sail:310-310`
- **Spec mention / defining-location candidate:** `src/priv/machine.adoc:2419` (architectural concept evidence). Normative anchor: `norm:mtvec_mode_enc`.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** No unique semantic UDB YAML match established; this is a Sail-only record.
## `base.writable_fiom`
- **Class:** `0b101`
- **Sail identity:** `base.writable_fiom`; hierarchy level `base`
- **Schema:** `/properties/base/properties/writable_fiom`; type `boolean`; definition `{"description":"core/sys_regs.sail:86.38-86.63","type":"boolean"}`
- **Sail source evidence:** `model/core/sys_regs.sail:86-86`
- **Spec mention / defining-location candidate:** `src/priv/machine.adoc:2139` (architectural concept evidence). Normative anchor: `norm:menvcfg_fiom_fence_op`.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** No unique semantic UDB YAML match established; this is a Sail-only record.
## `extensions.V.support_level`
- **Class:** `0b101`
- **Sail identity:** `extensions.V.support_level`; hierarchy level `extensions.V`
- **Schema:** `/properties/extensions/properties/V/properties/support_level`; type `string`; definition `{"description":"core/vlen.sail:18.44-18.77","enum":["Disabled","Float_double","Float_single","Full","Integer"],"type":"string"}`
- **Sail source evidence:** `model/core/vlen.sail:18-18`
- **Spec mention / defining-location candidate:** `src/priv/hypervisor.adoc:1` (extension and setting terms); no normative anchor confidently identified.
- **Defining status:** Spec mention found; first defining location remains unresolved.
- **UDB match:** No unique semantic UDB YAML match established; this is a Sail-only record.
## `platform.clock_frequency`
- **Class:** `0b101`
- **Sail identity:** `platform.clock_frequency`; hierarchy level `platform`
- **Schema:** `/properties/platform/properties/clock_frequency`; type `integer`; definition `{"description":"postlude/device_tree.sail:188.25-188.56","minimum":0,"type":"integer"}`
- **Sail source evidence:** `model/postlude/device_tree.sail:188-188`
- **Spec mention / defining-location candidate:** `src/priv/machine.adoc:2539` (exact setting phrase); no normative anchor confidently identified.
- **Defining status:** Spec mention found; first defining location remains unresolved.
- **UDB match:** No unique semantic UDB YAML match established; this is a Sail-only record.
## `platform.hartid`
- **Class:** `0b101`
- **Sail identity:** `platform.hartid`; hierarchy level `platform`
- **Schema:** `/properties/platform/properties/hartid`; type `integer`; definition `{"allOf":[{"description":"core/sys_regs.sail:880.48-880.70","type":"integer"},{"description":"postlude/validate_config.sail:1214.23-1214.45","type":"integer"}]}`
- **Sail source evidence:** `model/core/sys_regs.sail:880-880`, `model/postlude/validate_config.sail:1214-1214`
- **Spec mention / defining-location candidate:** `src/priv/machine.adoc:308` (architectural concept evidence). Normative anchor: `norm:mhartid_sz_acc_op`.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** No unique semantic UDB YAML match established; this is a Sail-only record.
## `platform.wfi_is_nop`
- **Class:** `0b101`
- **Sail identity:** `platform.wfi_is_nop`; hierarchy level `platform`
- **Schema:** `/properties/platform/properties/wfi_is_nop`; type `boolean`; definition `{"description":"postlude/step.sail:239.20-239.46","type":"boolean"}`
- **Sail source evidence:** `model/postlude/step.sail:239-239`
- **Spec mention / defining-location candidate:** `src/priv/machine.adoc:2705` (architectural concept evidence). Normative anchor: `norm:wfi_resume_reason`.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** No unique semantic UDB YAML match established; this is a Sail-only record.
- **Near-match review:** WFI_U_MODE is different: U-mode availability of WFI is not equivalent to treating WFI as a NOP.
