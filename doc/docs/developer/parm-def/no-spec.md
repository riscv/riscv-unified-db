# UDB and Sail, no spec (`0b110`)

Parameters: **41**

## `DBG_HCONTEXT_WIDTH`

- **Class:** `0b110`
- **UDB YAML:** `spec/std/isa/param/DBG_HCONTEXT_WIDTH.yaml`
- **Sail match/evidence:** extensions.Sdtrig.hcontext.width → /properties/extensions/properties/Sdtrig/properties/hcontext/properties/width [model/extensions/Sdtrig/sdtrig_regs.sail:132]
- **Spec evidence/anchor:** —
## `DBG_SCONTEXT_WIDTH`

- **Class:** `0b110`
- **UDB YAML:** `spec/std/isa/param/DBG_SCONTEXT_WIDTH.yaml`
- **Sail match/evidence:** extensions.Sdtrig.scontext.width → /properties/extensions/properties/Sdtrig/properties/scontext/properties/width [model/extensions/Sdtrig/sdtrig_regs.sail:119]
- **Spec evidence/anchor:** —
## `extensions.S.supported`
- **Class:** `0b110`
- **UDB extension declaration:** `spec/std/isa/ext/S.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.S.supported`; hierarchy level `extensions.S`
- **Schema:** `/properties/extensions/properties/S/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:63.38-63.67","type":"boolean"},{"description":"postlude/validate_config.sail:10.6-10.35","type":"boolean"},{"description":"postlude/validate_config.sail:26.6-26.35","type":"boolean"},{"description":"postlude/validate_config.sail:87.8-87.37","type":"boolean"},{"description":"postlude/validate_config.sail:269.6-269.35","type":"boolean"},{"description":"postlude/validate_config.sail:152.8-152.37","type":"boolean"},{"description":"postlude/validate_config.sail:145.11-145.40","type":"boolean"},{"description":"postlude/validate_config.sail:202.8-202.37","type":"boolean"},{"description":"postlude/validate_config.sail:197.11-197.40","type":"boolean"},{"description":"postlude/validate_config.sail:997.73-997.102","type":"boolean"},{"description":"postlude/validate_config.sail:993.13-993.42","type":"boolean"},{"description":"postlude/validate_config.sail:944.57-944.86","type":"boolean"},{"description":"postlude/validate_config.sail:851.11-851.40","type":"boolean"},{"description":"postlude/validate_config.sail:842.66-842.95","type":"boolean"},{"description":"postlude/validate_config.sail:838.57-838.86","type":"boolean"},{"description":"postlude/validate_config.sail:802.63-802.92","type":"boolean"},{"description":"postlude/validate_config.sail:771.11-771.40","type":"boolean"},{"description":"postlude/validate_config.sail:757.11-757.40","type":"boolean"},{"description":"postlude/validate_config.sail:705.11-705.40","type":"boolean"},{"description":"postlude/validate_config.sail:1060.6-1060.35","type":"boolean"},{"description":"postlude/validate_config.sail:1251.16-1251.45","type":"boolean"},{"description":"postlude/validate_config.sail:1238.16-1238.45","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:63-63`, `model/postlude/validate_config.sail:10-10`, `model/postlude/validate_config.sail:26-26`, `model/postlude/validate_config.sail:87-87`, `model/postlude/validate_config.sail:269-269`, `model/postlude/validate_config.sail:152-152`, `model/postlude/validate_config.sail:145-145`, `model/postlude/validate_config.sail:202-202`, `model/postlude/validate_config.sail:197-197`, `model/postlude/validate_config.sail:997-997`, `model/postlude/validate_config.sail:993-993`, `model/postlude/validate_config.sail:944-944`, `model/postlude/validate_config.sail:851-851`, `model/postlude/validate_config.sail:842-842`, `model/postlude/validate_config.sail:838-838`, `model/postlude/validate_config.sail:802-802`, `model/postlude/validate_config.sail:771-771`, `model/postlude/validate_config.sail:757-757`, `model/postlude/validate_config.sail:705-705`, `model/postlude/validate_config.sail:1060-1060`, `model/postlude/validate_config.sail:1251-1251`, `model/postlude/validate_config.sail:1238-1238`
- **Spec mention / defining-location candidate:** No semantic match established in the searched AsciiDoc corpus.
- **Defining status:** No spec match or defining location established.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Sdtrig.supported`
- **Class:** `0b110`
- **UDB extension declaration:** `spec/std/isa/ext/Sdtrig.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Sdtrig.supported`; hierarchy level `extensions.Sdtrig`
- **Schema:** `/properties/extensions/properties/Sdtrig/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:535.43-535.77","type":"boolean"},{"description":"postlude/validate_config.sail:948.6-948.40","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:535-535`, `model/postlude/validate_config.sail:948-948`
- **Spec mention / defining-location candidate:** No semantic match established in the searched AsciiDoc corpus.
- **Defining status:** No spec match or defining location established.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Smmpm.supported`
- **Class:** `0b110`
- **UDB extension declaration:** `spec/std/isa/ext/Smmpm.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Smmpm.supported`; hierarchy level `extensions.Smmpm`
- **Schema:** `/properties/extensions/properties/Smmpm/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:637.42-637.75","type":"boolean"},{"description":"postlude/validate_config.sail:798.51-798.84","type":"boolean"},{"description":"postlude/validate_config.sail:815.33-815.66","type":"boolean"},{"description":"postlude/validate_config.sail:827.33-827.66","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:637-637`, `model/postlude/validate_config.sail:798-798`, `model/postlude/validate_config.sail:815-815`, `model/postlude/validate_config.sail:827-827`
- **Spec mention / defining-location candidate:** No semantic match established in the searched AsciiDoc corpus.
- **Defining status:** No spec match or defining location established.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Smnpm.supported`
- **Class:** `0b110`
- **UDB extension declaration:** `spec/std/isa/ext/Smnpm.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Smnpm.supported`; hierarchy level `extensions.Smnpm`
- **Schema:** `/properties/extensions/properties/Smnpm/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:642.42-642.75","type":"boolean"},{"description":"postlude/validate_config.sail:798.96-798.129","type":"boolean"},{"description":"postlude/validate_config.sail:814.33-814.66","type":"boolean"},{"description":"postlude/validate_config.sail:826.33-826.66","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:642-642`, `model/postlude/validate_config.sail:798-798`, `model/postlude/validate_config.sail:814-814`, `model/postlude/validate_config.sail:826-826`
- **Spec mention / defining-location candidate:** No semantic match established in the searched AsciiDoc corpus.
- **Defining status:** No spec match or defining location established.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Ssnpm.supported`
- **Class:** `0b110`
- **UDB extension declaration:** `spec/std/isa/ext/Ssnpm.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Ssnpm.supported`; hierarchy level `extensions.Ssnpm`
- **Schema:** `/properties/extensions/properties/Ssnpm/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:520.42-520.75","type":"boolean"},{"description":"postlude/validate_config.sail:798.6-798.39","type":"boolean"},{"description":"postlude/validate_config.sail:802.15-802.48","type":"boolean"},{"description":"postlude/validate_config.sail:813.79-813.112","type":"boolean"},{"description":"postlude/validate_config.sail:825.79-825.112","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:520-520`, `model/postlude/validate_config.sail:798-798`, `model/postlude/validate_config.sail:802-802`, `model/postlude/validate_config.sail:813-813`, `model/postlude/validate_config.sail:825-825`
- **Spec mention / defining-location candidate:** No semantic match established in the searched AsciiDoc corpus.
- **Defining status:** No spec match or defining location established.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Svukte.supported`
- **Class:** `0b110`
- **UDB extension declaration:** `spec/std/isa/ext/Svukte.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Svukte.supported`; hierarchy level `extensions.Svukte`
- **Schema:** `/properties/extensions/properties/Svukte/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:619.82-619.116","type":"boolean"},{"description":"postlude/validate_config.sail:256.6-256.40","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:619-619`, `model/postlude/validate_config.sail:256-256`
- **Spec mention / defining-location candidate:** No semantic match established in the searched AsciiDoc corpus.
- **Defining status:** No spec match or defining location established.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.U.supported`
- **Class:** `0b110`
- **UDB extension declaration:** `spec/std/isa/ext/U.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.U.supported`; hierarchy level `extensions.U`
- **Schema:** `/properties/extensions/properties/U/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:67.38-67.67","type":"boolean"},{"description":"postlude/validate_config.sail:10.50-10.79","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:67-67`, `model/postlude/validate_config.sail:10-10`
- **Spec mention / defining-location candidate:** No semantic match established in the searched AsciiDoc corpus.
- **Defining status:** No spec match or defining location established.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zibi.supported`
- **Class:** `0b110`
- **UDB extension declaration:** `spec/std/isa/ext/Zibi.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zibi.supported`; hierarchy level `extensions.Zibi`
- **Schema:** `/properties/extensions/properties/Zibi/properties/supported`; type `boolean`; definition `{"description":"core/extensions.sail:115.80-115.112","type":"boolean"}`
- **Sail source evidence:** `model/core/extensions.sail:115-115`
- **Spec mention / defining-location candidate:** No semantic match established in the searched AsciiDoc corpus.
- **Defining status:** No spec match or defining location established.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zilx.supported`
- **Class:** `0b110`
- **UDB extension declaration:** `spec/std/isa/ext/Zilx.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zilx.supported`; hierarchy level `extensions.Zilx`
- **Schema:** `/properties/extensions/properties/Zilx/properties/supported`; type `boolean`; definition `{"description":"core/extensions.sail:172.80-172.112","type":"boolean"}`
- **Sail source evidence:** `model/core/extensions.sail:172-172`
- **Spec mention / defining-location candidate:** No semantic match established in the searched AsciiDoc corpus.
- **Defining status:** No spec match or defining location established.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zvabd.supported`
- **Class:** `0b110`
- **UDB extension declaration:** `spec/std/isa/ext/Zvabd.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zvabd.supported`; hierarchy level `extensions.Zvabd`
- **Schema:** `/properties/extensions/properties/Zvabd/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:401.81-401.114","type":"boolean"},{"description":"postlude/validate_config.sail:408.6-408.39","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:401-401`, `model/postlude/validate_config.sail:408-408`
- **Spec mention / defining-location candidate:** No semantic match established in the searched AsciiDoc corpus.
- **Defining status:** No spec match or defining location established.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `HSTATEEN0_C_TYPE`
- **Class:** `0b110`
- **UDB YAML:** `spec/std/isa/param/HSTATEEN0_C_TYPE.yaml`
- **Sail identity:** `extensions.Stateen.hstateen0.C`; hierarchy level `extensions.Stateen.hstateen0`
- **Schema:** `/properties/extensions/properties/Stateen/properties/hstateen0/properties/C`; type `string`; definition `{"description":"core/platform_config.sail:141.39-141.76","enum":["CSRBit_ReadOnlyOne","CSRBit_ReadOnlyZero","CSRBit_Writable"],"type":"string"}`
- **Sail source evidence:** `model/core/platform_config.sail:141-141`
- **Spec mention / defining-location candidate:** No semantic match established in the searched AsciiDoc corpus.
- **Defining status:** No spec match or defining location established.
- **UDB match:** Semantic match to Sail `extensions.Stateen.hstateen0.C`; UDB `name`, `long_name`, and definition agree with the setting's behavior.
## `MSTATEEN0_C_TYPE`
- **Class:** `0b110`
- **UDB YAML:** `spec/std/isa/param/MSTATEEN0_C_TYPE.yaml`
- **Sail identity:** `extensions.Stateen.mstateen0.C`; hierarchy level `extensions.Stateen.mstateen0`
- **Schema:** `/properties/extensions/properties/Stateen/properties/mstateen0/properties/C`; type `string`; definition `{"description":"core/platform_config.sail:132.39-132.76","enum":["CSRBit_ReadOnlyOne","CSRBit_ReadOnlyZero","CSRBit_Writable"],"type":"string"}`
- **Sail source evidence:** `model/core/platform_config.sail:132-132`
- **Spec mention / defining-location candidate:** No semantic match established in the searched AsciiDoc corpus.
- **Defining status:** No spec match or defining location established.
- **UDB match:** Semantic match to Sail `extensions.Stateen.mstateen0.C`; UDB `name`, `long_name`, and definition agree with the setting's behavior.
## `MSTATEEN0_P1P13_TYPE`
- **Class:** `0b110`
- **UDB YAML:** `spec/std/isa/param/MSTATEEN0_P1P13_TYPE.yaml`
- **Sail identity:** `extensions.Stateen.mstateen0.P1P13`; hierarchy level `extensions.Stateen.mstateen0`
- **Schema:** `/properties/extensions/properties/Stateen/properties/mstateen0/properties/P1P13`; type `string`; definition `{"description":"core/platform_config.sail:129.39-129.80","enum":["CSRBit_ReadOnlyOne","CSRBit_ReadOnlyZero","CSRBit_Writable"],"type":"string"}`
- **Sail source evidence:** `model/core/platform_config.sail:129-129`
- **Spec mention / defining-location candidate:** No semantic match established in the searched AsciiDoc corpus.
- **Defining status:** No spec match or defining location established.
- **UDB match:** Semantic match to Sail `extensions.Stateen.mstateen0.P1P13`; UDB `name`, `long_name`, and definition agree with the setting's behavior.
## `MSTATEEN0_SRMCFG_TYPE`
- **Class:** `0b110`
- **UDB YAML:** `spec/std/isa/param/MSTATEEN0_SRMCFG_TYPE.yaml`
- **Sail identity:** `extensions.Stateen.mstateen0.SRMCFG`; hierarchy level `extensions.Stateen.mstateen0`
- **Schema:** `/properties/extensions/properties/Stateen/properties/mstateen0/properties/SRMCFG`; type `string`; definition `{"description":"core/platform_config.sail:130.39-130.81","enum":["CSRBit_ReadOnlyOne","CSRBit_ReadOnlyZero","CSRBit_Writable"],"type":"string"}`
- **Sail source evidence:** `model/core/platform_config.sail:130-130`
- **Spec mention / defining-location candidate:** No semantic match established in the searched AsciiDoc corpus.
- **Defining status:** No spec match or defining location established.
- **UDB match:** Semantic match to Sail `extensions.Stateen.mstateen0.SRMCFG`; UDB `name`, `long_name`, and definition agree with the setting's behavior.
## `SDTRIG_BREAKPOINT_REENTRANCY`

- **Class:** `0b110`
- **UDB YAML:** `spec/std/isa/param/SDTRIG_BREAKPOINT_REENTRANCY.yaml`
- **Sail match/evidence:** extensions.Sdtrig.breakpoint_reentrancy → /properties/extensions/properties/Sdtrig/properties/breakpoint_reentrancy [model/core/platform_config.sail:251]
- **Spec evidence/anchor:** —
## `SDTRIG_ETRIGGER_SUPPORTED_EXCEPTIONS`

- **Class:** `0b110`
- **UDB YAML:** `spec/std/isa/param/SDTRIG_ETRIGGER_SUPPORTED_EXCEPTIONS.yaml`
- **Sail match/evidence:** extensions.Sdtrig.etrigger.supported_exceptions → /properties/extensions/properties/Sdtrig/properties/etrigger/properties/supported_exceptions [model/core/platform_config.sail:231]
- **Spec evidence/anchor:** —
## `SDTRIG_ETRIGGER_SUPPORTED_TRIGGERS`

- **Class:** `0b110`
- **UDB YAML:** `spec/std/isa/param/SDTRIG_ETRIGGER_SUPPORTED_TRIGGERS.yaml`
- **Sail match/evidence:** extensions.Sdtrig.etrigger.supported → /properties/extensions/properties/Sdtrig/properties/etrigger/properties/supported [model/core/platform_config.sail:15]
- **Spec evidence/anchor:** —
## `SDTRIG_ICOUNT_COUNT_HARDWIRED_1`

- **Class:** `0b110`
- **UDB YAML:** `spec/std/isa/param/SDTRIG_ICOUNT_COUNT_HARDWIRED_1.yaml`
- **Sail match/evidence:** extensions.Sdtrig.icount.count_hardwired_one → /properties/extensions/properties/Sdtrig/properties/icount/properties/count_hardwired_one [model/extensions/Sdtrig/sdtrig_types.sail:433]
- **Spec evidence/anchor:** —
## `SDTRIG_ICOUNT_SELF_WRITE_SETS_PENDING`

- **Class:** `0b110`
- **UDB YAML:** `spec/std/isa/param/SDTRIG_ICOUNT_SELF_WRITE_SETS_PENDING.yaml`
- **Sail match/evidence:** extensions.Sdtrig.icount.self_write_sets_pending → /properties/extensions/properties/Sdtrig/properties/icount/properties/self_write_sets_pending [model/extensions/Sdtrig/sdtrig_types.sail:434]
- **Spec evidence/anchor:** —
## `SDTRIG_ICOUNT_SUPPORTED_TRIGGERS`

- **Class:** `0b110`
- **UDB YAML:** `spec/std/isa/param/SDTRIG_ICOUNT_SUPPORTED_TRIGGERS.yaml`
- **Sail match/evidence:** extensions.Sdtrig.icount.supported → /properties/extensions/properties/Sdtrig/properties/icount/properties/supported [model/core/platform_config.sail:230]
- **Spec evidence/anchor:** —
## `SDTRIG_ITRIGGER_SUPPORTED_INTERRUPTS`

- **Class:** `0b110`
- **UDB YAML:** `spec/std/isa/param/SDTRIG_ITRIGGER_SUPPORTED_INTERRUPTS.yaml`
- **Sail match/evidence:** extensions.Sdtrig.itrigger.supported_interrupts → /properties/extensions/properties/Sdtrig/properties/itrigger/properties/supported_interrupts [model/core/platform_config.sail:232]
- **Spec evidence/anchor:** —
## `SDTRIG_ITRIGGER_SUPPORTED_TRIGGERS`

- **Class:** `0b110`
- **UDB YAML:** `spec/std/isa/param/SDTRIG_ITRIGGER_SUPPORTED_TRIGGERS.yaml`
- **Sail match/evidence:** extensions.Sdtrig.itrigger.supported → /properties/extensions/properties/Sdtrig/properties/itrigger/properties/supported [model/core/platform_config.sail:15]
- **Spec evidence/anchor:** —
## `SDTRIG_M_WRITABLE`

- **Class:** `0b110`
- **UDB YAML:** `spec/std/isa/param/SDTRIG_M_WRITABLE.yaml`
- **Sail match/evidence:** fixed.Sdtrig.privilege_mode_trigger_bits [model/extensions/Sdtrig/sdtrig_types.sail:9]
- **Spec evidence/anchor:** —
## `SDTRIG_MAX_CHAIN_LENGTH`

- **Class:** `0b110`
- **UDB YAML:** `spec/std/isa/param/SDTRIG_MAX_CHAIN_LENGTH.yaml`
- **Sail match/evidence:** extensions.Sdtrig.mcontrol6.max_chain_length → /properties/extensions/properties/Sdtrig/properties/mcontrol6/properties/max_chain_length [model/core/platform_config.sail:238]
- **Spec evidence/anchor:** —
## `SDTRIG_MCONTROL6_EXECUTE_WRITABLE`

- **Class:** `0b110`
- **UDB YAML:** `spec/std/isa/param/SDTRIG_MCONTROL6_EXECUTE_WRITABLE.yaml`
- **Sail match/evidence:** extensions.Sdtrig.mcontrol6 → /properties/extensions/properties/Sdtrig/properties/mcontrol6 [model/extensions/Sdtrig/sdtrig_types.sail:24]
- **Spec evidence/anchor:** —
## `SDTRIG_MCONTROL6_MASKMAX6`

- **Class:** `0b110`
- **UDB YAML:** `spec/std/isa/param/SDTRIG_MCONTROL6_MASKMAX6.yaml`
- **Sail match/evidence:** extensions.Sdtrig.mcontrol6.maskmax6 → /properties/extensions/properties/Sdtrig/properties/mcontrol6/properties/maskmax6 [model/extensions/Sdtrig/sdtrig_types.sail:24]
- **Spec evidence/anchor:** —
## `SDTRIG_MCONTROL6_MATCH_LEGAL_VALUES`

- **Class:** `0b110`
- **UDB YAML:** `spec/std/isa/param/SDTRIG_MCONTROL6_MATCH_LEGAL_VALUES.yaml`
- **Sail match/evidence:** extensions.Sdtrig.mcontrol6 → /properties/extensions/properties/Sdtrig/properties/mcontrol6 [model/extensions/Sdtrig/sdtrig_types.sail:24]
- **Spec evidence/anchor:** —
## `SDTRIG_NUM_TRIGGERS`

- **Class:** `0b110`
- **UDB YAML:** `spec/std/isa/param/SDTRIG_NUM_TRIGGERS.yaml`
- **Sail match/evidence:** extensions.Sdtrig.num_triggers → /properties/extensions/properties/Sdtrig/properties/num_triggers [model/core/platform_config.sail:245]
- **Spec evidence/anchor:** —
## `SDTRIG_S_WRITABLE`

- **Class:** `0b110`
- **UDB YAML:** `spec/std/isa/param/SDTRIG_S_WRITABLE.yaml`
- **Sail match/evidence:** fixed.Sdtrig.privilege_mode_trigger_bits [model/extensions/Sdtrig/sdtrig_types.sail:9]
- **Spec evidence/anchor:** —
## `SDTRIG_TEXTRA_MHSELECT_MCONTEXT_MATCH`

- **Class:** `0b110`
- **UDB YAML:** `spec/std/isa/param/SDTRIG_TEXTRA_MHSELECT_MCONTEXT_MATCH.yaml`
- **Sail match/evidence:** extensions.Sdtrig.textra.mhselect.mcontext_match → /properties/extensions/properties/Sdtrig/properties/textra/properties/mhselect/properties/mcontext_match [model/extensions/Sdtrig/sdtrig_types.sail:236]
- **Spec evidence/anchor:** —
## `SDTRIG_TEXTRA_MHSELECT_VMID_MATCH`

- **Class:** `0b110`
- **UDB YAML:** `spec/std/isa/param/SDTRIG_TEXTRA_MHSELECT_VMID_MATCH.yaml`
- **Sail match/evidence:** extensions.Sdtrig.textra.mhselect.vmid_match → /properties/extensions/properties/Sdtrig/properties/textra/properties/mhselect/properties/vmid_match [model/extensions/Sdtrig/sdtrig_types.sail:237]
- **Spec evidence/anchor:** —
## `SDTRIG_TEXTRA_MHVALUE_LEN`

- **Class:** `0b110`
- **UDB YAML:** `spec/std/isa/param/SDTRIG_TEXTRA_MHVALUE_LEN.yaml`
- **Sail match/evidence:** extensions.Sdtrig.textra.mhvalue_len → /properties/extensions/properties/Sdtrig/properties/textra/properties/mhvalue_len [model/extensions/Sdtrig/sdtrig_types.sail:251]
- **Spec evidence/anchor:** —
## `SDTRIG_TEXTRA_SSELECT_ASID_MATCH`

- **Class:** `0b110`
- **UDB YAML:** `spec/std/isa/param/SDTRIG_TEXTRA_SSELECT_ASID_MATCH.yaml`
- **Sail match/evidence:** extensions.Sdtrig.textra.sselect.asid_match → /properties/extensions/properties/Sdtrig/properties/textra/properties/sselect/properties/asid_match [model/extensions/Sdtrig/sdtrig_types.sail:240]
- **Spec evidence/anchor:** —
## `SDTRIG_TEXTRA_SSELECT_SCONTEXT_MATCH`

- **Class:** `0b110`
- **UDB YAML:** `spec/std/isa/param/SDTRIG_TEXTRA_SSELECT_SCONTEXT_MATCH.yaml`
- **Sail match/evidence:** extensions.Sdtrig.textra.sselect.scontext_match → /properties/extensions/properties/Sdtrig/properties/textra/properties/sselect/properties/scontext_match [model/extensions/Sdtrig/sdtrig_types.sail:239]
- **Spec evidence/anchor:** —
## `SDTRIG_TEXTRA_SVALUE_LEN`

- **Class:** `0b110`
- **UDB YAML:** `spec/std/isa/param/SDTRIG_TEXTRA_SVALUE_LEN.yaml`
- **Sail match/evidence:** extensions.Sdtrig.textra.svalue_len → /properties/extensions/properties/Sdtrig/properties/textra/properties/svalue_len [model/extensions/Sdtrig/sdtrig_types.sail:252]
- **Spec evidence/anchor:** —
## `SDTRIG_U_WRITABLE`

- **Class:** `0b110`
- **UDB YAML:** `spec/std/isa/param/SDTRIG_U_WRITABLE.yaml`
- **Sail match/evidence:** fixed.Sdtrig.privilege_mode_trigger_bits [model/extensions/Sdtrig/sdtrig_types.sail:9]
- **Spec evidence/anchor:** —
## `SDTRIG_VS_WRITABLE`

- **Class:** `0b110`
- **UDB YAML:** `spec/std/isa/param/SDTRIG_VS_WRITABLE.yaml`
- **Sail match/evidence:** fixed.Sdtrig.privilege_mode_trigger_bits [model/extensions/Sdtrig/sdtrig_types.sail:9]
- **Spec evidence/anchor:** —
## `SDTRIG_VU_WRITABLE`

- **Class:** `0b110`
- **UDB YAML:** `spec/std/isa/param/SDTRIG_VU_WRITABLE.yaml`
- **Sail match/evidence:** fixed.Sdtrig.privilege_mode_trigger_bits [model/extensions/Sdtrig/sdtrig_types.sail:9]
- **Spec evidence/anchor:** —
## `SSTATEEN0_C_TYPE`
- **Class:** `0b110`
- **UDB YAML:** `spec/std/isa/param/SSTATEEN0_C_TYPE.yaml`
- **Sail identity:** `extensions.Stateen.sstateen0.C`; hierarchy level `extensions.Stateen.sstateen0`
- **Schema:** `/properties/extensions/properties/Stateen/properties/sstateen0/properties/C`; type `string`; definition `{"description":"core/platform_config.sail:144.39-144.76","enum":["CSRBit_ReadOnlyOne","CSRBit_ReadOnlyZero","CSRBit_Writable"],"type":"string"}`
- **Sail source evidence:** `model/core/platform_config.sail:144-144`
- **Spec mention / defining-location candidate:** No semantic match established in the searched AsciiDoc corpus.
- **Defining status:** No spec match or defining location established.
- **UDB match:** Semantic match to Sail `extensions.Stateen.sstateen0.C`; UDB `name`, `long_name`, and definition agree with the setting's behavior.
