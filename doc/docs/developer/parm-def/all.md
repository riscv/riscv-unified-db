# UDB, spec, and Sail (`0b111`)

Parameters: **343**

## `ARCH_ID_VALUE`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/ARCH_ID_VALUE.yaml`
- **Sail match/evidence:** platform.archid → /properties/platform/properties/archid [model/core/sys_regs.sail:879]
- **Spec evidence/anchor:** src/priv/machine.adoc:251 [norm:marchid_sz_acc_op]
## `ASID_WIDTH`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/ASID_WIDTH.yaml`
- **Sail match/evidence:** memory.asidlen → /properties/memory/properties/asidlen [model/core/xlen.sail:23]
- **Spec evidence/anchor:** src/priv/supervisor.adoc:1061 [norm:asidlen]
## `CACHE_BLOCK_SIZE`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/CACHE_BLOCK_SIZE.yaml`
- **Sail match/evidence:** platform.cache_block_size_exp → /properties/platform/properties/cache_block_size_exp [model/core/platform_config.sail:49]
- **Spec evidence/anchor:** src/unpriv/cmo.adoc:89 [norm:cache_block_size]
## `CONFIG_PTR_ADDRESS`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/CONFIG_PTR_ADDRESS.yaml`
- **Sail match/evidence:** memory.dtb_address → /properties/memory/properties/dtb_address [model/postlude/model.sail:38]
- **Spec evidence/anchor:** src/priv/machine.adoc:2096 [norm:mconfigptr_op]
## `COUNTINHIBIT_EN`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/COUNTINHIBIT_EN.yaml`
- **Sail match/evidence:** base.mcountinhibit.writable_bits → /properties/base/properties/mcountinhibit/properties/writable_bits [model/core/platform_config.sail:16]
- **Spec evidence/anchor:** src/priv/machine.adoc:1629 [norm:mcountinhibit_op2]
## `ELEN`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/ELEN.yaml`
- **Sail match/evidence:** extensions.V.elen_exp → /properties/extensions/properties/V/properties/elen_exp [model/extensions/V/vext_control.sail:29]
- **Spec evidence/anchor:** src/unpriv/vector-common.adoc:19 [norm:elen]
## `extensions.A.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/A.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.A.supported`; hierarchy level `extensions.A`
- **Schema:** `/properties/extensions/properties/A/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:214.126-214.155","type":"boolean"},{"description":"core/extensions.sail:211.125-211.154","type":"boolean"},{"description":"core/extensions.sail:41.38-41.67","type":"boolean"},{"description":"postlude/validate_config.sail:692.193-692.222","type":"boolean"},{"description":"postlude/validate_config.sail:667.100-667.129","type":"boolean"},{"description":"postlude/validate_config.sail:663.100-663.129","type":"boolean"},{"description":"postlude/validate_config.sail:1044.7-1044.36","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:214-214`, `model/core/extensions.sail:211-211`, `model/core/extensions.sail:41-41`, `model/postlude/validate_config.sail:692-692`, `model/postlude/validate_config.sail:667-667`, `model/postlude/validate_config.sail:663-663`, `model/postlude/validate_config.sail:1044-1044`
- **Spec mention / defining-location candidate:** `src/unpriv/a-st-ext.adoc:2` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.B.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/B.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.B.supported`; hierarchy level `extensions.B`
- **Schema:** `/properties/extensions/properties/B/properties/supported`; type `boolean`; definition `{"description":"core/extensions.sail:55.38-55.67","type":"boolean"}`
- **Sail source evidence:** `model/core/extensions.sail:55-55`
- **Spec mention / defining-location candidate:** `src/unpriv/b-st-ext.adoc:2` (extension-definition candidate). Normative anchor: `norm:b_extension_composition`.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.D.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/D.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.D.supported`; hierarchy level `extensions.D`
- **Schema:** `/properties/extensions/properties/D/properties/supported`; type `boolean`; definition `{"type":"boolean"}`
- **Sail source evidence:** `model/core/extensions.sail:47`, `model/core/flen.sail:9`, `model/core/flen.sail:11`
- **Spec mention / defining-location candidate:** `src/unpriv/d-st-ext.adoc:2` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.F.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/F.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.F.supported`; hierarchy level `extensions.F`
- **Schema:** `/properties/extensions/properties/F/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:45.38-45.67","type":"boolean"},{"description":"postlude/validate_config.sail:329.48-329.77","type":"boolean"},{"description":"postlude/validate_config.sail:635.9-635.38","type":"boolean"},{"description":"postlude/validate_config.sail:631.6-631.35","type":"boolean"},{"description":"postlude/validate_config.sail:1233.13-1233.42","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:45-45`, `model/postlude/validate_config.sail:329-329`, `model/postlude/validate_config.sail:635-635`, `model/postlude/validate_config.sail:631-631`, `model/postlude/validate_config.sail:1233-1233`
- **Spec mention / defining-location candidate:** `src/unpriv/f-st-ext.adoc:2` (extension-definition candidate). Normative anchor: `norm:f_ieee_compliance`.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.H.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/H.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.H.supported`; hierarchy level `extensions.H`
- **Schema:** `/properties/extensions/properties/H/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:71.38-71.67","type":"boolean"},{"description":"postlude/validate_config.sail:31.6-31.35","type":"boolean"},{"description":"postlude/validate_config.sail:93.50-93.79","type":"boolean"},{"description":"postlude/validate_config.sail:88.8-88.37","type":"boolean"},{"description":"postlude/validate_config.sail:275.6-275.35","type":"boolean"},{"description":"postlude/validate_config.sail:176.8-176.37","type":"boolean"},{"description":"postlude/validate_config.sail:212.8-212.37","type":"boolean"},{"description":"postlude/validate_config.sail:620.5-620.34","type":"boolean"},{"description":"postlude/validate_config.sail:988.74-988.103","type":"boolean"},{"description":"postlude/validate_config.sail:953.66-953.95","type":"boolean"},{"description":"postlude/validate_config.sail:935.47-935.76","type":"boolean"},{"description":"postlude/validate_config.sail:922.11-922.40","type":"boolean"},{"description":"postlude/validate_config.sail:910.11-910.40","type":"boolean"},{"description":"postlude/validate_config.sail:900.11-900.40","type":"boolean"},{"description":"postlude/validate_config.sail:888.11-888.40","type":"boolean"},{"description":"postlude/validate_config.sail:878.11-878.40","type":"boolean"},{"description":"postlude/validate_config.sail:846.6-846.35","type":"boolean"},{"description":"postlude/validate_config.sail:781.11-781.40","type":"boolean"},{"description":"postlude/validate_config.sail:740.11-740.40","type":"boolean"},{"description":"postlude/validate_config.sail:725.8-725.37","type":"boolean"},{"description":"postlude/validate_config.sail:1139.62-1139.91","type":"boolean"},{"description":"postlude/validate_config.sail:1118.6-1118.35","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:71-71`, `model/postlude/validate_config.sail:31-31`, `model/postlude/validate_config.sail:93-93`, `model/postlude/validate_config.sail:88-88`, `model/postlude/validate_config.sail:275-275`, `model/postlude/validate_config.sail:176-176`, `model/postlude/validate_config.sail:212-212`, `model/postlude/validate_config.sail:620-620`, `model/postlude/validate_config.sail:988-988`, `model/postlude/validate_config.sail:953-953`, `model/postlude/validate_config.sail:935-935`, `model/postlude/validate_config.sail:922-922`, `model/postlude/validate_config.sail:910-910`, `model/postlude/validate_config.sail:900-900`, `model/postlude/validate_config.sail:888-888`, `model/postlude/validate_config.sail:878-878`, `model/postlude/validate_config.sail:846-846`, `model/postlude/validate_config.sail:781-781`, `model/postlude/validate_config.sail:740-740`, `model/postlude/validate_config.sail:725-725`, `model/postlude/validate_config.sail:1139-1139`, `model/postlude/validate_config.sail:1118-1118`
- **Spec mention / defining-location candidate:** `src/priv/hypervisor.adoc:2` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.M.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/M.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.M.supported`; hierarchy level `extensions.M`
- **Schema:** `/properties/extensions/properties/M/properties/supported`; type `boolean`; definition `{"description":"core/extensions.sail:37.38-37.67","type":"boolean"}`
- **Sail source evidence:** `model/core/extensions.sail:37-37`
- **Spec mention / defining-location candidate:** `src/unpriv/m-st-ext.adoc:2` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Sha.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Sha.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Sha.supported`; hierarchy level `extensions.Sha`
- **Schema:** `/properties/extensions/properties/Sha/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:75.40-75.71","type":"boolean"},{"description":"postlude/validate_config.sail:934.6-934.37","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:75-75`, `model/postlude/validate_config.sail:934-934`
- **Spec mention / defining-location candidate:** `src/priv/priv-preface.adoc:64` (extension mention; defining location unresolved); no normative anchor confidently identified.
- **Defining status:** Spec mention found; first defining location remains unresolved.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Shcounterenw.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Shcounterenw.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Shcounterenw.supported`; hierarchy level `extensions.Shcounterenw`
- **Schema:** `/properties/extensions/properties/Shcounterenw/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:79.49-79.89","type":"boolean"},{"description":"postlude/validate_config.sail:937.58-937.98","type":"boolean"},{"description":"postlude/validate_config.sail:780.6-780.46","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:79-79`, `model/postlude/validate_config.sail:937-937`, `model/postlude/validate_config.sail:780-780`
- **Spec mention / defining-location candidate:** `src/priv/priv-preface.adoc:59` (extension mention; defining location unresolved); no normative anchor confidently identified.
- **Defining status:** Spec mention found; first defining location remains unresolved.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Shgatpa.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Shgatpa.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Shgatpa.supported`; hierarchy level `extensions.Shgatpa`
- **Schema:** `/properties/extensions/properties/Shgatpa/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:85.44-85.79","type":"boolean"},{"description":"postlude/validate_config.sail:938.53-938.88","type":"boolean"},{"description":"postlude/validate_config.sail:877.6-877.41","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:85-85`, `model/postlude/validate_config.sail:938-938`, `model/postlude/validate_config.sail:877-877`
- **Spec mention / defining-location candidate:** `src/priv/priv-preface.adoc:63` (extension mention; defining location unresolved); no normative anchor confidently identified.
- **Defining status:** Spec mention found; first defining location remains unresolved.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Shlcofideleg.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Shlcofideleg.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Shlcofideleg.supported`; hierarchy level `extensions.Shlcofideleg`
- **Schema:** `/properties/extensions/properties/Shlcofideleg/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:90.49-90.89","type":"boolean"},{"description":"postlude/validate_config.sail:887.6-887.46","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:90-90`, `model/postlude/validate_config.sail:887-887`
- **Spec mention / defining-location candidate:** `src/priv/priv-preface.adoc:57` (extension mention; defining location unresolved); no normative anchor confidently identified.
- **Defining status:** Spec mention found; first defining location remains unresolved.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Shtvala.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Shtvala.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Shtvala.supported`; hierarchy level `extensions.Shtvala`
- **Schema:** `/properties/extensions/properties/Shtvala/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:94.44-94.79","type":"boolean"},{"description":"postlude/validate_config.sail:939.53-939.88","type":"boolean"},{"description":"postlude/validate_config.sail:899.6-899.41","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:94-94`, `model/postlude/validate_config.sail:939-939`, `model/postlude/validate_config.sail:899-899`
- **Spec mention / defining-location candidate:** `src/priv/priv-preface.adoc:61` (extension mention; defining location unresolved); no normative anchor confidently identified.
- **Defining status:** Spec mention found; first defining location remains unresolved.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Shvsatpa.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Shvsatpa.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Shvsatpa.supported`; hierarchy level `extensions.Shvsatpa`
- **Schema:** `/properties/extensions/properties/Shvsatpa/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:99.45-99.81","type":"boolean"},{"description":"postlude/validate_config.sail:940.54-940.90","type":"boolean"},{"description":"postlude/validate_config.sail:921.6-921.42","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:99-99`, `model/postlude/validate_config.sail:940-940`, `model/postlude/validate_config.sail:921-921`
- **Spec mention / defining-location candidate:** `src/priv/priv-preface.adoc:62` (extension mention; defining location unresolved); no normative anchor confidently identified.
- **Defining status:** Spec mention found; first defining location remains unresolved.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Shvstvala.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Shvstvala.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Shvstvala.supported`; hierarchy level `extensions.Shvstvala`
- **Schema:** `/properties/extensions/properties/Shvstvala/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:104.46-104.83","type":"boolean"},{"description":"postlude/validate_config.sail:941.55-941.92","type":"boolean"},{"description":"postlude/validate_config.sail:739.6-739.43","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:104-104`, `model/postlude/validate_config.sail:941-941`, `model/postlude/validate_config.sail:739-739`
- **Spec mention / defining-location candidate:** `src/priv/priv-preface.adoc:60` (extension mention; defining location unresolved); no normative anchor confidently identified.
- **Defining status:** Spec mention found; first defining location remains unresolved.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Shvstvecd.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Shvstvecd.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Shvstvecd.supported`; hierarchy level `extensions.Shvstvecd`
- **Schema:** `/properties/extensions/properties/Shvstvecd/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:110.46-110.83","type":"boolean"},{"description":"postlude/validate_config.sail:942.55-942.92","type":"boolean"},{"description":"postlude/validate_config.sail:909.6-909.43","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:110-110`, `model/postlude/validate_config.sail:942-942`, `model/postlude/validate_config.sail:909-909`
- **Spec mention / defining-location candidate:** `src/priv/priv-preface.adoc:58` (extension mention; defining location unresolved); no normative anchor confidently identified.
- **Defining status:** Spec mention found; first defining location remains unresolved.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Smcntrpmf.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Smcntrpmf.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Smcntrpmf.supported`; hierarchy level `extensions.Smcntrpmf`
- **Schema:** `/properties/extensions/properties/Smcntrpmf/properties/supported`; type `boolean`; definition `{"description":"core/extensions.sail:628.46-628.83","type":"boolean"}`
- **Sail source evidence:** `model/core/extensions.sail:628-628`
- **Spec mention / defining-location candidate:** `src/priv/smcntrpmf.adoc:3` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Smdbltrp.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Smdbltrp.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Smdbltrp.supported`; hierarchy level `extensions.Smdbltrp`
- **Schema:** `/properties/extensions/properties/Smdbltrp/properties/supported`; type `boolean`; definition `{"description":"core/extensions.sail:632.45-632.81","type":"boolean"}`
- **Sail source evidence:** `model/core/extensions.sail:632-632`
- **Spec mention / defining-location candidate:** `src/priv/smdbltrp.adoc:2` (extension-definition candidate). Normative anchor: `norm:Smdbltrp_with_Smrnmi_op`.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Ssccptr.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Ssccptr.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Ssccptr.supported`; hierarchy level `extensions.Ssccptr`
- **Schema:** `/properties/extensions/properties/Ssccptr/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:504.44-504.79","type":"boolean"},{"description":"postlude/validate_config.sail:229.6-229.41","type":"boolean"},{"description":"postlude/validate_config.sail:562.17-562.52","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:504-504`, `model/postlude/validate_config.sail:229-229`, `model/postlude/validate_config.sail:562-562`
- **Spec mention / defining-location candidate:** `src/priv/priv-preface.adoc:47` (extension mention; defining location unresolved); no normative anchor confidently identified.
- **Defining status:** Spec mention found; first defining location remains unresolved.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Sscofpmf.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Sscofpmf.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Sscofpmf.supported`; hierarchy level `extensions.Sscofpmf`
- **Schema:** `/properties/extensions/properties/Sscofpmf/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:508.45-508.81","type":"boolean"},{"description":"postlude/validate_config.sail:892.11-892.47","type":"boolean"},{"description":"postlude/validate_config.sail:857.6-857.42","type":"boolean"},{"description":"postlude/validate_config.sail:860.16-860.52","type":"boolean"},{"description":"postlude/validate_config.sail:1105.42-1105.78","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:508-508`, `model/postlude/validate_config.sail:892-892`, `model/postlude/validate_config.sail:857-857`, `model/postlude/validate_config.sail:860-860`, `model/postlude/validate_config.sail:1105-1105`
- **Spec mention / defining-location candidate:** `src/priv/sscofpmf.adoc:2` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Sscounterenw.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Sscounterenw.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Sscounterenw.supported`; hierarchy level `extensions.Sscounterenw`
- **Schema:** `/properties/extensions/properties/Sscounterenw/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:512.49-512.89","type":"boolean"},{"description":"postlude/validate_config.sail:770.6-770.46","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:512-512`, `model/postlude/validate_config.sail:770-770`
- **Spec mention / defining-location candidate:** `src/priv/priv-preface.adoc:50` (extension mention; defining location unresolved); no normative anchor confidently identified.
- **Defining status:** Spec mention found; first defining location remains unresolved.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Ssdbltrp.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Ssdbltrp.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Ssdbltrp.supported`; hierarchy level `extensions.Ssdbltrp`
- **Schema:** `/properties/extensions/properties/Ssdbltrp/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:516.45-516.81","type":"boolean"},{"description":"postlude/validate_config.sail:944.6-944.42","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:516-516`, `model/postlude/validate_config.sail:944-944`
- **Spec mention / defining-location candidate:** `src/priv/ssdbltrp.adoc:2` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Ssqosid.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Ssqosid.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Ssqosid.supported`; hierarchy level `extensions.Ssqosid`
- **Schema:** `/properties/extensions/properties/Ssqosid/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:652.44-652.79","type":"boolean"},{"description":"postlude/validate_config.sail:766.6-766.41","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:652-652`, `model/postlude/validate_config.sail:766-766`
- **Spec mention / defining-location candidate:** `src/priv/ssqosid.adoc:2` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Ssstrict.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Ssstrict.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Ssstrict.supported`; hierarchy level `extensions.Ssstrict`
- **Schema:** `/properties/extensions/properties/Ssstrict/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:529.45-529.81","type":"boolean"},{"description":"postlude/validate_config.sail:838.6-838.42","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:529-529`, `model/postlude/validate_config.sail:838-838`
- **Spec mention / defining-location candidate:** `src/priv/priv-preface.adoc:51` (extension mention; defining location unresolved); no normative anchor confidently identified.
- **Defining status:** Spec mention found; first defining location remains unresolved.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Sstc.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Sstc.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Sstc.supported`; hierarchy level `extensions.Sstc`
- **Schema:** `/properties/extensions/properties/Sstc/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:558.41-558.73","type":"boolean"},{"description":"postlude/validate_config.sail:1111.8-1111.40","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:558-558`, `model/postlude/validate_config.sail:1111-1111`
- **Spec mention / defining-location candidate:** `src/priv/sstc.adoc:2` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Sstvala.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Sstvala.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Sstvala.supported`; hierarchy level `extensions.Sstvala`
- **Schema:** `/properties/extensions/properties/Sstvala/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:562.44-562.79","type":"boolean"},{"description":"postlude/validate_config.sail:704.6-704.41","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:562-562`, `model/postlude/validate_config.sail:704-704`
- **Spec mention / defining-location candidate:** `src/priv/priv-preface.adoc:49` (extension mention; defining location unresolved); no normative anchor confidently identified.
- **Defining status:** Spec mention found; first defining location remains unresolved.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Sstvecd.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Sstvecd.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Sstvecd.supported`; hierarchy level `extensions.Sstvecd`
- **Schema:** `/properties/extensions/properties/Sstvecd/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:568.44-568.79","type":"boolean"},{"description":"postlude/validate_config.sail:756.6-756.41","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:568-568`, `model/postlude/validate_config.sail:756-756`
- **Spec mention / defining-location candidate:** `src/priv/priv-preface.adoc:48` (extension mention; defining location unresolved); no normative anchor confidently identified.
- **Defining status:** Spec mention found; first defining location remains unresolved.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Sv32.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Sv32.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Sv32.supported`; hierarchy level `extensions.Sv32`
- **Schema:** `/properties/extensions/properties/Sv32/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:581.41-581.73","type":"boolean"},{"description":"postlude/validate_config.sail:40.9-40.41","type":"boolean"},{"description":"postlude/validate_config.sail:168.8-168.40","type":"boolean"},{"description":"postlude/validate_config.sail:202.99-202.131","type":"boolean"},{"description":"postlude/validate_config.sail:197.52-197.84","type":"boolean"},{"description":"postlude/validate_config.sail:926.49-926.81","type":"boolean"},{"description":"postlude/validate_config.sail:882.48-882.80","type":"boolean"},{"description":"postlude/validate_config.sail:1134.26-1134.58","type":"boolean"},{"description":"postlude/validate_config.sail:1269.54-1269.86","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:581-581`, `model/postlude/validate_config.sail:40-40`, `model/postlude/validate_config.sail:168-168`, `model/postlude/validate_config.sail:202-202`, `model/postlude/validate_config.sail:197-197`, `model/postlude/validate_config.sail:926-926`, `model/postlude/validate_config.sail:882-882`, `model/postlude/validate_config.sail:1134-1134`, `model/postlude/validate_config.sail:1269-1269`
- **Spec mention / defining-location candidate:** `src/priv/hypervisor.adoc:27` (named translation mode); no normative anchor confidently identified.
- **Defining status:** Spec mention found; first defining location remains unresolved.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
- **Near-match review:** SV32_VSMODE_TRANSLATION and SV32X4_TRANSLATION describe specific VS-mode and x4 modes, not the top-level Sv32 support flag.
## `extensions.Sv39.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Sv39.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Sv39.supported`; hierarchy level `extensions.Sv39`
- **Schema:** `/properties/extensions/properties/Sv39/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:584.41-584.73","type":"boolean"},{"description":"postlude/validate_config.sail:103.9-103.41","type":"boolean"},{"description":"postlude/validate_config.sail:163.55-163.87","type":"boolean"},{"description":"postlude/validate_config.sail:153.57-153.89","type":"boolean"},{"description":"postlude/validate_config.sail:145.141-145.173","type":"boolean"},{"description":"postlude/validate_config.sail:207.8-207.40","type":"boolean"},{"description":"postlude/validate_config.sail:927.49-927.81","type":"boolean"},{"description":"postlude/validate_config.sail:883.48-883.80","type":"boolean"},{"description":"postlude/validate_config.sail:1130.21-1130.53","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:584-584`, `model/postlude/validate_config.sail:103-103`, `model/postlude/validate_config.sail:163-163`, `model/postlude/validate_config.sail:153-153`, `model/postlude/validate_config.sail:145-145`, `model/postlude/validate_config.sail:207-207`, `model/postlude/validate_config.sail:927-927`, `model/postlude/validate_config.sail:883-883`, `model/postlude/validate_config.sail:1130-1130`
- **Spec mention / defining-location candidate:** `src/priv/hypervisor.adoc:28` (named translation mode); no normative anchor confidently identified.
- **Defining status:** Spec mention found; first defining location remains unresolved.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
- **Near-match review:** SV39_VSMODE_TRANSLATION and SV39X4_TRANSLATION describe specific VS-mode and x4 modes, not the top-level Sv39 support flag.
## `extensions.Sv48.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Sv48.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Sv48.supported`; hierarchy level `extensions.Sv48`
- **Schema:** `/properties/extensions/properties/Sv48/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:587.41-587.73","type":"boolean"},{"description":"postlude/validate_config.sail:163.8-163.40","type":"boolean"},{"description":"postlude/validate_config.sail:158.55-158.87","type":"boolean"},{"description":"postlude/validate_config.sail:153.101-153.133","type":"boolean"},{"description":"postlude/validate_config.sail:145.97-145.129","type":"boolean"},{"description":"postlude/validate_config.sail:207.52-207.84","type":"boolean"},{"description":"postlude/validate_config.sail:928.49-928.81","type":"boolean"},{"description":"postlude/validate_config.sail:884.48-884.80","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:587-587`, `model/postlude/validate_config.sail:163-163`, `model/postlude/validate_config.sail:158-158`, `model/postlude/validate_config.sail:153-153`, `model/postlude/validate_config.sail:145-145`, `model/postlude/validate_config.sail:207-207`, `model/postlude/validate_config.sail:928-928`, `model/postlude/validate_config.sail:884-884`
- **Spec mention / defining-location candidate:** `src/priv/hypervisor.adoc:946` (named translation mode); no normative anchor confidently identified.
- **Defining status:** Spec mention found; first defining location remains unresolved.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
- **Near-match review:** SV48_VSMODE_TRANSLATION and SV48X4_TRANSLATION describe specific VS-mode and x4 modes, not the top-level Sv48 support flag.
## `extensions.Sv57.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Sv57.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Sv57.supported`; hierarchy level `extensions.Sv57`
- **Schema:** `/properties/extensions/properties/Sv57/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:590.41-590.73","type":"boolean"},{"description":"postlude/validate_config.sail:158.8-158.40","type":"boolean"},{"description":"postlude/validate_config.sail:153.145-153.177","type":"boolean"},{"description":"postlude/validate_config.sail:145.53-145.85","type":"boolean"},{"description":"postlude/validate_config.sail:207.97-207.129","type":"boolean"},{"description":"postlude/validate_config.sail:929.49-929.81","type":"boolean"},{"description":"postlude/validate_config.sail:885.48-885.80","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:590-590`, `model/postlude/validate_config.sail:158-158`, `model/postlude/validate_config.sail:153-153`, `model/postlude/validate_config.sail:145-145`, `model/postlude/validate_config.sail:207-207`, `model/postlude/validate_config.sail:929-929`, `model/postlude/validate_config.sail:885-885`
- **Spec mention / defining-location candidate:** `src/priv/hypervisor.adoc:946` (named translation mode); no normative anchor confidently identified.
- **Defining status:** Spec mention found; first defining location remains unresolved.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
- **Near-match review:** SV57_VSMODE_TRANSLATION and SV57X4_TRANSLATION describe specific VS-mode and x4 modes, not the top-level Sv57 support flag.
## `extensions.Svade.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Svade.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Svade.supported`; hierarchy level `extensions.Svade`
- **Schema:** `/properties/extensions/properties/Svade/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:595.42-595.75","type":"boolean"},{"description":"postlude/validate_config.sail:232.6-232.39","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:595-595`, `model/postlude/validate_config.sail:232-232`
- **Spec mention / defining-location candidate:** `src/priv/priv-preface.adoc:34` (extension mention; defining location unresolved); no normative anchor confidently identified.
- **Defining status:** Spec mention found; first defining location remains unresolved.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Svadu.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Svadu.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Svadu.supported`; hierarchy level `extensions.Svadu`
- **Schema:** `/properties/extensions/properties/Svadu/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:599.42-599.75","type":"boolean"},{"description":"postlude/validate_config.sail:235.6-235.39","type":"boolean"},{"description":"postlude/validate_config.sail:563.17-563.50","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:599-599`, `model/postlude/validate_config.sail:235-235`, `model/postlude/validate_config.sail:563-563`
- **Spec mention / defining-location candidate:** `src/priv/svadu.adoc:2` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Svinval.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Svinval.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Svinval.supported`; hierarchy level `extensions.Svinval`
- **Schema:** `/properties/extensions/properties/Svinval/properties/supported`; type `boolean`; definition `{"description":"core/extensions.sail:603.44-603.79","type":"boolean"}`
- **Sail source evidence:** `model/core/extensions.sail:603-603`
- **Spec mention / defining-location candidate:** `src/priv/svinval.adoc:2` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Svnapot.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Svnapot.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Svnapot.supported`; hierarchy level `extensions.Svnapot`
- **Schema:** `/properties/extensions/properties/Svnapot/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:607.44-607.79","type":"boolean"},{"description":"postlude/validate_config.sail:247.6-247.41","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:607-607`, `model/postlude/validate_config.sail:247-247`
- **Spec mention / defining-location candidate:** `src/priv/svnapot.adoc:2` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Svpbmt.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Svpbmt.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Svpbmt.supported`; hierarchy level `extensions.Svpbmt`
- **Schema:** `/properties/extensions/properties/Svpbmt/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:611.43-611.77","type":"boolean"},{"description":"postlude/validate_config.sail:238.6-238.40","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:611-611`, `model/postlude/validate_config.sail:238-238`
- **Spec mention / defining-location candidate:** `src/priv/svpbmt.adoc:2` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Svrsw60t59b.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Svrsw60t59b.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Svrsw60t59b.supported`; hierarchy level `extensions.Svrsw60t59b`
- **Schema:** `/properties/extensions/properties/Svrsw60t59b/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:615.48-615.87","type":"boolean"},{"description":"postlude/validate_config.sail:220.6-220.45","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:615-615`, `model/postlude/validate_config.sail:220-220`
- **Spec mention / defining-location candidate:** `src/priv/svrsw60t59b.adoc:2` (extension-definition candidate). Normative anchor: `norm:Svrsw60t59b_reserved_bits_60_59`.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Svvptc.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Svvptc.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Svvptc.supported`; hierarchy level `extensions.Svvptc`
- **Schema:** `/properties/extensions/properties/Svvptc/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:623.43-623.77","type":"boolean"},{"description":"postlude/validate_config.sail:265.6-265.40","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:623-623`, `model/postlude/validate_config.sail:265-265`
- **Spec mention / defining-location candidate:** `src/priv/svvptc.adoc:2` (extension-definition candidate). Normative anchor: `norm:Svvptc_explicit_stores_update_valid_bit`.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zaamo.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Zaamo.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zaamo.supported`; hierarchy level `extensions.Zaamo`
- **Schema:** `/properties/extensions/properties/Zaamo/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:186.42-186.75","type":"boolean"},{"description":"postlude/validate_config.sail:692.148-692.181","type":"boolean"},{"description":"postlude/validate_config.sail:667.55-667.88","type":"boolean"},{"description":"postlude/validate_config.sail:663.55-663.88","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:186-186`, `model/postlude/validate_config.sail:692-692`, `model/postlude/validate_config.sail:667-667`, `model/postlude/validate_config.sail:663-663`
- **Spec mention / defining-location candidate:** `src/unpriv/zaamo.adoc:2` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zabha.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Zabha.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zabha.supported`; hierarchy level `extensions.Zabha`
- **Schema:** `/properties/extensions/properties/Zabha/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:190.42-190.75","type":"boolean"},{"description":"postlude/validate_config.sail:663.6-663.39","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:190-190`, `model/postlude/validate_config.sail:663-663`
- **Spec mention / defining-location candidate:** `src/unpriv/zabha.adoc:2` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zacas.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Zacas.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zacas.supported`; hierarchy level `extensions.Zacas`
- **Schema:** `/properties/extensions/properties/Zacas/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:194.42-194.75","type":"boolean"},{"description":"postlude/validate_config.sail:667.6-667.39","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:194-194`, `model/postlude/validate_config.sail:667-667`
- **Spec mention / defining-location candidate:** `src/unpriv/zacas.adoc:2` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zalrsc.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Zalrsc.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zalrsc.supported`; hierarchy level `extensions.Zalrsc`
- **Schema:** `/properties/extensions/properties/Zalrsc/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:214.82-214.116","type":"boolean"},{"description":"core/extensions.sail:211.81-211.115","type":"boolean"},{"description":"core/extensions.sail:198.43-198.77","type":"boolean"},{"description":"postlude/validate_config.sail:1044.48-1044.82","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:214-214`, `model/core/extensions.sail:211-211`, `model/core/extensions.sail:198-198`, `model/postlude/validate_config.sail:1044-1044`
- **Spec mention / defining-location candidate:** `src/unpriv/zalrsc.adoc:2` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zama16b.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Zama16b.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zama16b.supported`; hierarchy level `extensions.Zama16b`
- **Schema:** `/properties/extensions/properties/Zama16b/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:202.44-202.79","type":"boolean"},{"description":"postlude/validate_config.sail:556.17-556.52","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:202-202`, `model/postlude/validate_config.sail:556-556`
- **Spec mention / defining-location candidate:** `src/unpriv/zama.adoc:2` (extension-definition candidate). Normative anchor: `norm:zama16b_mag`.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zawrs.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Zawrs.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zawrs.supported`; hierarchy level `extensions.Zawrs`
- **Schema:** `/properties/extensions/properties/Zawrs/properties/supported`; type `boolean`; definition `{"description":"core/extensions.sail:207.42-207.75","type":"boolean"}`
- **Sail source evidence:** `model/core/extensions.sail:207-207`
- **Spec mention / defining-location candidate:** `src/unpriv/zawrs.adoc:2` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zba.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Zba.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zba.supported`; hierarchy level `extensions.Zba`
- **Schema:** `/properties/extensions/properties/Zba/properties/supported`; type `boolean`; definition `{"description":"core/extensions.sail:274.40-274.71","type":"boolean"}`
- **Sail source evidence:** `model/core/extensions.sail:274-274`
- **Spec mention / defining-location candidate:** `src/unpriv/zba.adoc:2` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zbb.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Zbb.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zbb.supported`; hierarchy level `extensions.Zbb`
- **Schema:** `/properties/extensions/properties/Zbb/properties/supported`; type `boolean`; definition `{"description":"core/extensions.sail:278.40-278.71","type":"boolean"}`
- **Sail source evidence:** `model/core/extensions.sail:278-278`
- **Spec mention / defining-location candidate:** `src/unpriv/zbb.adoc:2` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zbc.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Zbc.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zbc.supported`; hierarchy level `extensions.Zbc`
- **Schema:** `/properties/extensions/properties/Zbc/properties/supported`; type `boolean`; definition `{"description":"core/extensions.sail:282.40-282.71","type":"boolean"}`
- **Sail source evidence:** `model/core/extensions.sail:282-282`
- **Spec mention / defining-location candidate:** `src/unpriv/zbc.adoc:2` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zbkb.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Zbkb.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zbkb.supported`; hierarchy level `extensions.Zbkb`
- **Schema:** `/properties/extensions/properties/Zbkb/properties/supported`; type `boolean`; definition `{"description":"core/extensions.sail:286.41-286.73","type":"boolean"}`
- **Sail source evidence:** `model/core/extensions.sail:286-286`
- **Spec mention / defining-location candidate:** `src/unpriv/zbkb.adoc:2` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zbkc.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Zbkc.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zbkc.supported`; hierarchy level `extensions.Zbkc`
- **Schema:** `/properties/extensions/properties/Zbkc/properties/supported`; type `boolean`; definition `{"description":"core/extensions.sail:290.41-290.73","type":"boolean"}`
- **Sail source evidence:** `model/core/extensions.sail:290-290`
- **Spec mention / defining-location candidate:** `src/unpriv/zbkc.adoc:2` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zbkx.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Zbkx.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zbkx.supported`; hierarchy level `extensions.Zbkx`
- **Schema:** `/properties/extensions/properties/Zbkx/properties/supported`; type `boolean`; definition `{"description":"core/extensions.sail:294.41-294.73","type":"boolean"}`
- **Sail source evidence:** `model/core/extensions.sail:294-294`
- **Spec mention / defining-location candidate:** `src/unpriv/zbkx.adoc:2` (extension-definition candidate). Normative anchor: `norm:zbkx_lookup_table_model`.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zbs.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Zbs.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zbs.supported`; hierarchy level `extensions.Zbs`
- **Schema:** `/properties/extensions/properties/Zbs/properties/supported`; type `boolean`; definition `{"description":"core/extensions.sail:298.40-298.71","type":"boolean"}`
- **Sail source evidence:** `model/core/extensions.sail:298-298`
- **Spec mention / defining-location candidate:** `src/unpriv/zbs.adoc:2` (extension-definition candidate). Normative anchor: `norm:zbs_single_bit_functionality`.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zca.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Zca.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zca.supported`; hierarchy level `extensions.Zca`
- **Schema:** `/properties/extensions/properties/Zca/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:245.40-245.71","type":"boolean"},{"description":"postlude/validate_config.sail:1139.106-1139.137","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:245-245`, `model/postlude/validate_config.sail:1139-1139`
- **Spec mention / defining-location candidate:** `src/unpriv/zca.adoc:2` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zcb.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Zcb.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zcb.supported`; hierarchy level `extensions.Zcb`
- **Schema:** `/properties/extensions/properties/Zcb/properties/supported`; type `boolean`; definition `{"description":"core/extensions.sail:249.40-249.71","type":"boolean"}`
- **Sail source evidence:** `model/core/extensions.sail:249-249`
- **Spec mention / defining-location candidate:** `src/unpriv/zcb.adoc:2` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zcd.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Zcd.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zcd.supported`; hierarchy level `extensions.Zcd`
- **Schema:** `/properties/extensions/properties/Zcd/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:253.40-253.71","type":"boolean"},{"description":"postlude/validate_config.sail:657.6-657.37","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:253-253`, `model/postlude/validate_config.sail:657-657`
- **Spec mention / defining-location candidate:** `src/unpriv/zcd.adoc:2` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zcf.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Zcf.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zcf.supported`; hierarchy level `extensions.Zcf`
- **Schema:** `/properties/extensions/properties/Zcf/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:257.40-257.71","type":"boolean"},{"description":"postlude/validate_config.sail:652.8-652.39","type":"boolean"},{"description":"postlude/validate_config.sail:627.6-627.37","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:257-257`, `model/postlude/validate_config.sail:652-652`, `model/postlude/validate_config.sail:627-627`
- **Spec mention / defining-location candidate:** `src/unpriv/zcf.adoc:2` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zcmop.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Zcmop.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zcmop.supported`; hierarchy level `extensions.Zcmop`
- **Schema:** `/properties/extensions/properties/Zcmop/properties/supported`; type `boolean`; definition `{"description":"core/extensions.sail:261.42-261.75","type":"boolean"}`
- **Sail source evidence:** `model/core/extensions.sail:261-261`
- **Spec mention / defining-location candidate:** `src/unpriv/zcmop.adoc:2` (extension-definition candidate). Normative anchor: `norm:Zcmop_op`.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zdinx.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Zdinx.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zdinx.supported`; hierarchy level `extensions.Zdinx`
- **Schema:** `/properties/extensions/properties/Zdinx/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:240.42-240.75","type":"boolean"},{"description":"postlude/validate_config.sail:675.6-675.39","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:240-240`, `model/postlude/validate_config.sail:675-675`
- **Spec mention / defining-location candidate:** `src/unpriv/zfinx.adoc:2` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zfa.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Zfa.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zfa.supported`; hierarchy level `extensions.Zfa`
- **Schema:** `/properties/extensions/properties/Zfa/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:219.40-219.71","type":"boolean"},{"description":"postlude/validate_config.sail:636.8-636.39","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:219-219`, `model/postlude/validate_config.sail:636-636`
- **Spec mention / defining-location candidate:** `src/unpriv/zfa.adoc:2` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zfbfmin.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Zfbfmin.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zfbfmin.supported`; hierarchy level `extensions.Zfbfmin`
- **Schema:** `/properties/extensions/properties/Zfbfmin/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:223.44-223.79","type":"boolean"},{"description":"postlude/validate_config.sail:700.58-700.93","type":"boolean"},{"description":"postlude/validate_config.sail:648.8-648.43","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:223-223`, `model/postlude/validate_config.sail:700-700`, `model/postlude/validate_config.sail:648-648`
- **Spec mention / defining-location candidate:** `src/unpriv/zfbfmin.adoc:2` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zfh.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Zfh.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zfh.supported`; hierarchy level `extensions.Zfh`
- **Schema:** `/properties/extensions/properties/Zfh/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:227.40-227.71","type":"boolean"},{"description":"postlude/validate_config.sail:640.8-640.39","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:227-227`, `model/postlude/validate_config.sail:640-640`
- **Spec mention / defining-location candidate:** `src/unpriv/zfh.adoc:2` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zfhmin.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Zfhmin.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zfhmin.supported`; hierarchy level `extensions.Zfhmin`
- **Schema:** `/properties/extensions/properties/Zfhmin/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:231.43-231.77","type":"boolean"},{"description":"postlude/validate_config.sail:363.86-363.120","type":"boolean"},{"description":"postlude/validate_config.sail:644.8-644.42","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:231-231`, `model/postlude/validate_config.sail:363-363`, `model/postlude/validate_config.sail:644-644`
- **Spec mention / defining-location candidate:** `src/unpriv/zfhmin.adoc:2` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zfinx.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Zfinx.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zfinx.supported`; hierarchy level `extensions.Zfinx`
- **Schema:** `/properties/extensions/properties/Zfinx/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:235.42-235.75","type":"boolean"},{"description":"postlude/validate_config.sail:683.57-683.90","type":"boolean"},{"description":"postlude/validate_config.sail:679.54-679.87","type":"boolean"},{"description":"postlude/validate_config.sail:675.54-675.87","type":"boolean"},{"description":"postlude/validate_config.sail:671.6-671.39","type":"boolean"},{"description":"postlude/validate_config.sail:631.47-631.80","type":"boolean"},{"description":"postlude/validate_config.sail:1166.7-1166.40","type":"boolean"},{"description":"postlude/validate_config.sail:1228.6-1228.39","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:235-235`, `model/postlude/validate_config.sail:683-683`, `model/postlude/validate_config.sail:679-679`, `model/postlude/validate_config.sail:675-675`, `model/postlude/validate_config.sail:671-671`, `model/postlude/validate_config.sail:631-631`, `model/postlude/validate_config.sail:1166-1166`, `model/postlude/validate_config.sail:1228-1228`
- **Spec mention / defining-location candidate:** `src/unpriv/zfinx.adoc:2` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zhinx.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Zhinx.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zhinx.supported`; hierarchy level `extensions.Zhinx`
- **Schema:** `/properties/extensions/properties/Zhinx/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:356.42-356.75","type":"boolean"},{"description":"postlude/validate_config.sail:679.6-679.39","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:356-356`, `model/postlude/validate_config.sail:679-679`
- **Spec mention / defining-location candidate:** `src/unpriv/zfinx.adoc:2` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zhinxmin.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Zhinxmin.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zhinxmin.supported`; hierarchy level `extensions.Zhinxmin`
- **Schema:** `/properties/extensions/properties/Zhinxmin/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:360.45-360.81","type":"boolean"},{"description":"postlude/validate_config.sail:683.6-683.42","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:360-360`, `model/postlude/validate_config.sail:683-683`
- **Spec mention / defining-location candidate:** `src/unpriv/zfinx.adoc:2` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zic64b.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Zic64b.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zic64b.supported`; hierarchy level `extensions.Zic64b`
- **Schema:** `/properties/extensions/properties/Zic64b/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:119.43-119.77","type":"boolean"},{"description":"postlude/validate_config.sail:1039.6-1039.40","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:119-119`, `model/postlude/validate_config.sail:1039-1039`
- **Spec mention / defining-location candidate:** `src/unpriv/zic64b.adoc:2` (extension-definition candidate). Normative anchor: `norm:zic64b_cache_block_size`.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zicbom.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Zicbom.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zicbom.supported`; hierarchy level `extensions.Zicbom`
- **Schema:** `/properties/extensions/properties/Zicbom/properties/supported`; type `boolean`; definition `{"description":"core/extensions.sail:124.43-124.77","type":"boolean"}`
- **Sail source evidence:** `model/core/extensions.sail:124-124`
- **Spec mention / defining-location candidate:** `src/unpriv/cmo.adoc:662` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zicbop.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Zicbop.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zicbop.supported`; hierarchy level `extensions.Zicbop`
- **Schema:** `/properties/extensions/properties/Zicbop/properties/supported`; type `boolean`; definition `{"description":"core/extensions.sail:128.43-128.77","type":"boolean"}`
- **Sail source evidence:** `model/core/extensions.sail:128-128`
- **Spec mention / defining-location candidate:** `src/unpriv/cmo.adoc:772` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zicboz.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Zicboz.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zicboz.supported`; hierarchy level `extensions.Zicboz`
- **Schema:** `/properties/extensions/properties/Zicboz/properties/supported`; type `boolean`; definition `{"description":"core/extensions.sail:132.43-132.77","type":"boolean"}`
- **Sail source evidence:** `model/core/extensions.sail:132-132`
- **Spec mention / defining-location candidate:** `src/unpriv/cmo.adoc:737` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Ziccamoa.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Ziccamoa.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Ziccamoa.supported`; hierarchy level `extensions.Ziccamoa`
- **Schema:** `/properties/extensions/properties/Ziccamoa/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:303.45-303.81","type":"boolean"},{"description":"postlude/validate_config.sail:557.17-557.53","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:303-303`, `model/postlude/validate_config.sail:557-557`
- **Spec mention / defining-location candidate:** `src/unpriv/ziccamoa.adoc:2` (extension-definition candidate). Normative anchor: `norm:ziccamoa_amo_pma`.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Ziccamoc.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Ziccamoc.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Ziccamoc.supported`; hierarchy level `extensions.Ziccamoc`
- **Schema:** `/properties/extensions/properties/Ziccamoc/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:307.45-307.81","type":"boolean"},{"description":"postlude/validate_config.sail:558.17-558.53","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:307-307`, `model/postlude/validate_config.sail:558-558`
- **Spec mention / defining-location candidate:** `src/unpriv/ziccamoc.adoc:2` (extension-definition candidate). Normative anchor: `norm:ziccamoc_casq_pma`.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Ziccif.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Ziccif.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Ziccif.supported`; hierarchy level `extensions.Ziccif`
- **Schema:** `/properties/extensions/properties/Ziccif/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:311.43-311.77","type":"boolean"},{"description":"postlude/validate_config.sail:559.17-559.51","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:311-311`, `model/postlude/validate_config.sail:559-559`
- **Spec mention / defining-location candidate:** `src/unpriv/ziccif.adoc:2` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zicclsm.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Zicclsm.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zicclsm.supported`; hierarchy level `extensions.Zicclsm`
- **Schema:** `/properties/extensions/properties/Zicclsm/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:316.44-316.79","type":"boolean"},{"description":"postlude/validate_config.sail:560.17-560.52","type":"boolean"},{"description":"postlude/validate_config.sail:1050.6-1050.41","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:316-316`, `model/postlude/validate_config.sail:560-560`, `model/postlude/validate_config.sail:1050-1050`
- **Spec mention / defining-location candidate:** `src/unpriv/zicclsm.adoc:2` (extension-definition candidate). Normative anchor: `norm:zicclsm_misaligned_support`.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Ziccrse.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Ziccrse.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Ziccrse.supported`; hierarchy level `extensions.Ziccrse`
- **Schema:** `/properties/extensions/properties/Ziccrse/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:321.44-321.79","type":"boolean"},{"description":"postlude/validate_config.sail:561.17-561.52","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:321-321`, `model/postlude/validate_config.sail:561-561`
- **Spec mention / defining-location candidate:** `src/unpriv/ziccrse.adoc:2` (extension-definition candidate). Normative anchor: `norm:ziccrse_rsrv_eventual`.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zicfilp.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Zicfilp.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zicfilp.supported`; hierarchy level `extensions.Zicfilp`
- **Schema:** `/properties/extensions/properties/Zicfilp/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:136.44-136.79","type":"boolean"},{"description":"postlude/validate_config.sail:687.6-687.41","type":"boolean"},{"description":"postlude/validate_config.sail:1070.140-1070.175","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:136-136`, `model/postlude/validate_config.sail:687-687`, `model/postlude/validate_config.sail:1070-1070`
- **Spec mention / defining-location candidate:** `src/priv/priv-cfi.adoc:11` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zicfiss.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Zicfiss.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zicfiss.supported`; hierarchy level `extensions.Zicfiss`
- **Schema:** `/properties/extensions/properties/Zicfiss/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:140.44-140.79","type":"boolean"},{"description":"postlude/validate_config.sail:692.6-692.41","type":"boolean"},{"description":"postlude/validate_config.sail:1070.90-1070.125","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:140-140`, `model/postlude/validate_config.sail:692-692`, `model/postlude/validate_config.sail:1070-1070`
- **Spec mention / defining-location candidate:** `src/priv/priv-cfi.adoc:124` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zicond.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Zicond.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zicond.supported`; hierarchy level `extensions.Zicond`
- **Schema:** `/properties/extensions/properties/Zicond/properties/supported`; type `boolean`; definition `{"description":"core/extensions.sail:148.43-148.77","type":"boolean"}`
- **Sail source evidence:** `model/core/extensions.sail:148-148`
- **Spec mention / defining-location candidate:** `src/unpriv/zicond.adoc:2` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zicsr.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Zicsr.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zicsr.supported`; hierarchy level `extensions.Zicsr`
- **Schema:** `/properties/extensions/properties/Zicsr/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:152.42-152.75","type":"boolean"},{"description":"postlude/validate_config.sail:343.36-343.69","type":"boolean"},{"description":"postlude/validate_config.sail:766.56-766.89","type":"boolean"},{"description":"postlude/validate_config.sail:692.57-692.90","type":"boolean"},{"description":"postlude/validate_config.sail:687.56-687.89","type":"boolean"},{"description":"postlude/validate_config.sail:671.54-671.87","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:152-152`, `model/postlude/validate_config.sail:343-343`, `model/postlude/validate_config.sail:766-766`, `model/postlude/validate_config.sail:692-692`, `model/postlude/validate_config.sail:687-687`, `model/postlude/validate_config.sail:671-671`
- **Spec mention / defining-location candidate:** `src/unpriv/zicsr.adoc:2` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zifencei.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Zifencei.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zifencei.supported`; hierarchy level `extensions.Zifencei`
- **Schema:** `/properties/extensions/properties/Zifencei/properties/supported`; type `boolean`; definition `{"description":"core/extensions.sail:156.45-156.81","type":"boolean"}`
- **Sail source evidence:** `model/core/extensions.sail:156-156`
- **Spec mention / defining-location candidate:** `src/unpriv/zifencei.adoc:2` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zihintntl.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Zihintntl.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zihintntl.supported`; hierarchy level `extensions.Zihintntl`
- **Schema:** `/properties/extensions/properties/Zihintntl/properties/supported`; type `boolean`; definition `{"description":"core/extensions.sail:160.46-160.83","type":"boolean"}`
- **Sail source evidence:** `model/core/extensions.sail:160-160`
- **Spec mention / defining-location candidate:** `src/unpriv/zihintntl.adoc:2` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zihintpause.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Zihintpause.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zihintpause.supported`; hierarchy level `extensions.Zihintpause`
- **Schema:** `/properties/extensions/properties/Zihintpause/properties/supported`; type `boolean`; definition `{"description":"core/extensions.sail:164.48-164.87","type":"boolean"}`
- **Sail source evidence:** `model/core/extensions.sail:164-164`
- **Spec mention / defining-location candidate:** `src/unpriv/zihintpause.adoc:2` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zihpm.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Zihpm.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zihpm.supported`; hierarchy level `extensions.Zihpm`
- **Schema:** `/properties/extensions/properties/Zihpm/properties/supported`; type `boolean`; definition `{"description":"core/extensions.sail:168.42-168.75","type":"boolean"}`
- **Sail source evidence:** `model/core/extensions.sail:168-168`
- **Spec mention / defining-location candidate:** `src/unpriv/zihpm.adoc:2` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zimop.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Zimop.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zimop.supported`; hierarchy level `extensions.Zimop`
- **Schema:** `/properties/extensions/properties/Zimop/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:176.42-176.75","type":"boolean"},{"description":"postlude/validate_config.sail:692.102-692.135","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:176-176`, `model/postlude/validate_config.sail:692-692`
- **Spec mention / defining-location candidate:** `src/unpriv/zimop.adoc:2` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zknd.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Zknd.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zknd.supported`; hierarchy level `extensions.Zknd`
- **Schema:** `/properties/extensions/properties/Zknd/properties/supported`; type `boolean`; definition `{"description":"core/extensions.sail:326.41-326.73","type":"boolean"}`
- **Sail source evidence:** `model/core/extensions.sail:326-326`
- **Spec mention / defining-location candidate:** `src/unpriv/scalar-crypto.adoc:189` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zkne.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Zkne.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zkne.supported`; hierarchy level `extensions.Zkne`
- **Schema:** `/properties/extensions/properties/Zkne/properties/supported`; type `boolean`; definition `{"description":"core/extensions.sail:330.41-330.73","type":"boolean"}`
- **Sail source evidence:** `model/core/extensions.sail:330-330`
- **Spec mention / defining-location candidate:** `src/unpriv/scalar-crypto.adoc:217` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zknh.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Zknh.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zknh.supported`; hierarchy level `extensions.Zknh`
- **Schema:** `/properties/extensions/properties/Zknh/properties/supported`; type `boolean`; definition `{"description":"core/extensions.sail:334.41-334.73","type":"boolean"}`
- **Sail source evidence:** `model/core/extensions.sail:334-334`
- **Spec mention / defining-location candidate:** `src/unpriv/scalar-crypto.adoc:245` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zkr.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Zkr.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zkr.supported`; hierarchy level `extensions.Zkr`
- **Schema:** `/properties/extensions/properties/Zkr/properties/supported`; type `boolean`; definition `{"description":"core/extensions.sail:338.40-338.71","type":"boolean"}`
- **Sail source evidence:** `model/core/extensions.sail:338-338`
- **Spec mention / defining-location candidate:** `src/unpriv/scalar-crypto.adoc:309` (extension-definition candidate). Normative anchor: `norm:zkr_seed_addr`.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zksed.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Zksed.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zksed.supported`; hierarchy level `extensions.Zksed`
- **Schema:** `/properties/extensions/properties/Zksed/properties/supported`; type `boolean`; definition `{"description":"core/extensions.sail:342.42-342.75","type":"boolean"}`
- **Sail source evidence:** `model/core/extensions.sail:342-342`
- **Spec mention / defining-location candidate:** `src/unpriv/scalar-crypto.adoc:274` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zksh.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Zksh.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zksh.supported`; hierarchy level `extensions.Zksh`
- **Schema:** `/properties/extensions/properties/Zksh/properties/supported`; type `boolean`; definition `{"description":"core/extensions.sail:346.41-346.73","type":"boolean"}`
- **Sail source evidence:** `model/core/extensions.sail:346-346`
- **Spec mention / defining-location candidate:** `src/unpriv/scalar-crypto.adoc:293` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zkt.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Zkt.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zkt.supported`; hierarchy level `extensions.Zkt`
- **Schema:** `/properties/extensions/properties/Zkt/properties/supported`; type `boolean`; definition `{"description":"core/extensions.sail:350.40-350.71","type":"boolean"}`
- **Sail source evidence:** `model/core/extensions.sail:350-350`
- **Spec mention / defining-location candidate:** `src/unpriv/zkt.adoc:2` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zmmul.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Zmmul.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zmmul.supported`; hierarchy level `extensions.Zmmul`
- **Schema:** `/properties/extensions/properties/Zmmul/properties/supported`; type `boolean`; definition `{"description":"core/extensions.sail:181.42-181.75","type":"boolean"}`
- **Sail source evidence:** `model/core/extensions.sail:181-181`
- **Spec mention / defining-location candidate:** `src/unpriv/zmmul.adoc:2` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zvbb.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Zvbb.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zvbb.supported`; hierarchy level `extensions.Zvbb`
- **Schema:** `/properties/extensions/properties/Zvbb/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:422.41-422.73","type":"boolean"},{"description":"postlude/validate_config.sail:368.6-368.38","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:422-422`, `model/postlude/validate_config.sail:368-368`
- **Spec mention / defining-location candidate:** `src/unpriv/zvbb.adoc:2` (extension-definition candidate). Normative anchor: `norm:Zvbb_dependent_Zve32x`.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zvbc.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Zvbc.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zvbc.supported`; hierarchy level `extensions.Zvbc`
- **Schema:** `/properties/extensions/properties/Zvbc/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:426.41-426.73","type":"boolean"},{"description":"postlude/validate_config.sail:372.6-372.38","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:426-426`, `model/postlude/validate_config.sail:372-372`
- **Spec mention / defining-location candidate:** `src/unpriv/zvbc.adoc:2` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zvfbfmin.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Zvfbfmin.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zvfbfmin.supported`; hierarchy level `extensions.Zvfbfmin`
- **Schema:** `/properties/extensions/properties/Zvfbfmin/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:405.45-405.81","type":"boolean"},{"description":"postlude/validate_config.sail:700.108-700.144","type":"boolean"},{"description":"postlude/validate_config.sail:696.6-696.42","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:405-405`, `model/postlude/validate_config.sail:700-700`, `model/postlude/validate_config.sail:696-696`
- **Spec mention / defining-location candidate:** `src/unpriv/zvfbfmin.adoc:2` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zvfbfwma.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Zvfbfwma.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zvfbfwma.supported`; hierarchy level `extensions.Zvfbfwma`
- **Schema:** `/properties/extensions/properties/Zvfbfwma/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:409.45-409.81","type":"boolean"},{"description":"postlude/validate_config.sail:700.6-700.42","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:409-409`, `model/postlude/validate_config.sail:700-700`
- **Spec mention / defining-location candidate:** `src/unpriv/zvfbfwma.adoc:2` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zvfh.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Zvfh.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zvfh.supported`; hierarchy level `extensions.Zvfh`
- **Schema:** `/properties/extensions/properties/Zvfh/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:413.41-413.73","type":"boolean"},{"description":"postlude/validate_config.sail:363.6-363.38","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:413-413`, `model/postlude/validate_config.sail:363-363`
- **Spec mention / defining-location candidate:** `src/unpriv/zvfh.adoc:2` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zvfhmin.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Zvfhmin.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zvfhmin.supported`; hierarchy level `extensions.Zvfhmin`
- **Schema:** `/properties/extensions/properties/Zvfhmin/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:417.44-417.79","type":"boolean"},{"description":"postlude/validate_config.sail:359.6-359.41","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:417-417`, `model/postlude/validate_config.sail:359-359`
- **Spec mention / defining-location candidate:** `src/unpriv/zvfhmin.adoc:2` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zvkb.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Zvkb.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zvkb.supported`; hierarchy level `extensions.Zvkb`
- **Schema:** `/properties/extensions/properties/Zvkb/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:430.41-430.73","type":"boolean"},{"description":"postlude/validate_config.sail:376.6-376.38","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:430-430`, `model/postlude/validate_config.sail:376-376`
- **Spec mention / defining-location candidate:** `src/unpriv/vector-crypto.adoc:510` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zvkg.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Zvkg.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zvkg.supported`; hierarchy level `extensions.Zvkg`
- **Schema:** `/properties/extensions/properties/Zvkg/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:434.41-434.73","type":"boolean"},{"description":"postlude/validate_config.sail:380.6-380.38","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:434-434`, `model/postlude/validate_config.sail:380-380`
- **Spec mention / defining-location candidate:** `src/unpriv/vector-crypto.adoc:541` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zvkned.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Zvkned.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zvkned.supported`; hierarchy level `extensions.Zvkned`
- **Schema:** `/properties/extensions/properties/Zvkned/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:438.43-438.77","type":"boolean"},{"description":"postlude/validate_config.sail:384.6-384.40","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:438-438`, `model/postlude/validate_config.sail:384-384`
- **Spec mention / defining-location candidate:** `src/unpriv/vector-crypto.adoc:584` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zvknha.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Zvknha.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zvknha.supported`; hierarchy level `extensions.Zvknha`
- **Schema:** `/properties/extensions/properties/Zvknha/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:442.43-442.77","type":"boolean"},{"description":"postlude/validate_config.sail:388.6-388.40","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:442-442`, `model/postlude/validate_config.sail:388-388`
- **Spec mention / defining-location candidate:** `src/unpriv/vector-crypto.adoc:630` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zvknhb.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Zvknhb.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zvknhb.supported`; hierarchy level `extensions.Zvknhb`
- **Schema:** `/properties/extensions/properties/Zvknhb/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:446.43-446.77","type":"boolean"},{"description":"postlude/validate_config.sail:392.6-392.40","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:446-446`, `model/postlude/validate_config.sail:392-392`
- **Spec mention / defining-location candidate:** `src/unpriv/vector-crypto.adoc:630` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zvksed.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Zvksed.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zvksed.supported`; hierarchy level `extensions.Zvksed`
- **Schema:** `/properties/extensions/properties/Zvksed/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:450.43-450.77","type":"boolean"},{"description":"postlude/validate_config.sail:396.6-396.40","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:450-450`, `model/postlude/validate_config.sail:396-396`
- **Spec mention / defining-location candidate:** `src/unpriv/vector-crypto.adoc:704` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zvksh.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Zvksh.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zvksh.supported`; hierarchy level `extensions.Zvksh`
- **Schema:** `/properties/extensions/properties/Zvksh/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:454.42-454.75","type":"boolean"},{"description":"postlude/validate_config.sail:400.6-400.39","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:454-454`, `model/postlude/validate_config.sail:400-400`
- **Spec mention / defining-location candidate:** `src/unpriv/vector-crypto.adoc:749` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `extensions.Zvkt.supported`
- **Class:** `0b111`
- **UDB extension declaration:** `spec/std/isa/ext/Zvkt.yaml` (presence declaration, not a parameter YAML)
- **Sail identity:** `extensions.Zvkt.supported`; hierarchy level `extensions.Zvkt`
- **Schema:** `/properties/extensions/properties/Zvkt/properties/supported`; type `boolean`; definition `{"allOf":[{"description":"core/extensions.sail:458.41-458.73","type":"boolean"},{"description":"postlude/validate_config.sail:404.6-404.38","type":"boolean"}]}`
- **Sail source evidence:** `model/core/extensions.sail:458-458`, `model/postlude/validate_config.sail:404-404`
- **Spec mention / defining-location candidate:** `src/unpriv/vector-crypto.adoc:947` (extension-definition candidate); no normative anchor confidently identified.
- **Defining status:** Best first-definition/rule candidate.
- **UDB match:** Exact extension-support representation: the Sail `supported` leaf corresponds to the matching UDB extension YAML's presence.
## `FOLLOW_VTYPE_RESET_RECOMMENDATION`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/FOLLOW_VTYPE_RESET_RECOMMENDATION.yaml`
- **Sail match/evidence:** fixed.vector.reset_state [model/sys/sys_control.sail:608]
- **Spec evidence/anchor:** src/unpriv/vector-common.adoc:674 [reset recommendation]
## `GSTAGE_MODE_BARE`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/GSTAGE_MODE_BARE.yaml`
- **Sail match/evidence:** extensions.H.hgatp_modes → /properties/extensions/properties/H/properties/hgatp_modes [model/core/platform_config.sail:44]
- **Spec evidence/anchor:** src/priv/hypervisor.adoc:1911 [norm:hgatp_mode_bare_trans]
## `HCONTEXT_IMPLEMENTED`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/HCONTEXT_IMPLEMENTED.yaml`
- **Sail match/evidence:** extensions.Sdtrig.hcontext.supported → /properties/extensions/properties/Sdtrig/properties/hcontext/properties/supported [model/core/platform_config.sail:15]
- **Spec evidence/anchor:** src/priv/csrs.adoc:318 [CSR list]
## `HCOUNTENABLE_EN`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/HCOUNTENABLE_EN.yaml`
- **Sail match/evidence:** base.hcounteren_writable_bits → /properties/base/properties/hcounteren_writable_bits [model/core/sys_regs.sail:815]
- **Spec evidence/anchor:** src/priv/hypervisor.adoc:856 [norm:hcounteren_op]
## `HEDELEG_IAM_WRITABLE`
- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/HEDELEG_IAM_WRITABLE.yaml`
- **Sail identity:** `extensions.H.hedeleg_zero_writable`; hierarchy level `extensions.H`
- **Schema:** `/properties/extensions/properties/H/properties/hedeleg_zero_writable`; type `boolean`; definition `{"allOf":[{"description":"core/platform_config.sail:44.40-44.81","type":"boolean"},{"description":"postlude/validate_config.sail:1139.9-1139.50","type":"boolean"}]}`
- **Sail source evidence:** `model/core/platform_config.sail:44-44`, `model/postlude/validate_config.sail:1139-1139`
- **Spec evidence/anchor:** `src/priv/hypervisor.adoc:368-373` (`norm:hedeleg_acc`) requires `hedeleg.IAM` writable when IALIGN=32; Sail also parameterizes the optional IALIGN=16 case.
- **Defining status:** Normative rule found; the spec does not prescribe the optional IALIGN=16 choice.
- **UDB match:** Semantic match to Sail `extensions.H.hedeleg_zero_writable`; UDB `name`, `long_name`, and definition agree with the setting's behavior.
## `HPM_COUNTER10_WIDTH`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/HPM_COUNTER10_WIDTH.yaml`
- **Sail match/evidence:** base.hpmcounter_width_bits → /properties/base/properties/hpmcounter_width_bits [model/core/platform_config.sail:157]
- **Spec evidence/anchor:** src/priv/machine.adoc:1546 [norm:mhpmcounter_sz]
## `HPM_COUNTER11_WIDTH`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/HPM_COUNTER11_WIDTH.yaml`
- **Sail match/evidence:** base.hpmcounter_width_bits → /properties/base/properties/hpmcounter_width_bits [model/core/platform_config.sail:157]
- **Spec evidence/anchor:** src/priv/machine.adoc:1546 [norm:mhpmcounter_sz]
## `HPM_COUNTER12_WIDTH`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/HPM_COUNTER12_WIDTH.yaml`
- **Sail match/evidence:** base.hpmcounter_width_bits → /properties/base/properties/hpmcounter_width_bits [model/core/platform_config.sail:157]
- **Spec evidence/anchor:** src/priv/machine.adoc:1546 [norm:mhpmcounter_sz]
## `HPM_COUNTER13_WIDTH`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/HPM_COUNTER13_WIDTH.yaml`
- **Sail match/evidence:** base.hpmcounter_width_bits → /properties/base/properties/hpmcounter_width_bits [model/core/platform_config.sail:157]
- **Spec evidence/anchor:** src/priv/machine.adoc:1546 [norm:mhpmcounter_sz]
## `HPM_COUNTER14_WIDTH`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/HPM_COUNTER14_WIDTH.yaml`
- **Sail match/evidence:** base.hpmcounter_width_bits → /properties/base/properties/hpmcounter_width_bits [model/core/platform_config.sail:157]
- **Spec evidence/anchor:** src/priv/machine.adoc:1546 [norm:mhpmcounter_sz]
## `HPM_COUNTER15_WIDTH`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/HPM_COUNTER15_WIDTH.yaml`
- **Sail match/evidence:** base.hpmcounter_width_bits → /properties/base/properties/hpmcounter_width_bits [model/core/platform_config.sail:157]
- **Spec evidence/anchor:** src/priv/machine.adoc:1546 [norm:mhpmcounter_sz]
## `HPM_COUNTER16_WIDTH`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/HPM_COUNTER16_WIDTH.yaml`
- **Sail match/evidence:** base.hpmcounter_width_bits → /properties/base/properties/hpmcounter_width_bits [model/core/platform_config.sail:157]
- **Spec evidence/anchor:** src/priv/machine.adoc:1546 [norm:mhpmcounter_sz]
## `HPM_COUNTER17_WIDTH`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/HPM_COUNTER17_WIDTH.yaml`
- **Sail match/evidence:** base.hpmcounter_width_bits → /properties/base/properties/hpmcounter_width_bits [model/core/platform_config.sail:157]
- **Spec evidence/anchor:** src/priv/machine.adoc:1546 [norm:mhpmcounter_sz]
## `HPM_COUNTER18_WIDTH`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/HPM_COUNTER18_WIDTH.yaml`
- **Sail match/evidence:** base.hpmcounter_width_bits → /properties/base/properties/hpmcounter_width_bits [model/core/platform_config.sail:157]
- **Spec evidence/anchor:** src/priv/machine.adoc:1546 [norm:mhpmcounter_sz]
## `HPM_COUNTER19_WIDTH`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/HPM_COUNTER19_WIDTH.yaml`
- **Sail match/evidence:** base.hpmcounter_width_bits → /properties/base/properties/hpmcounter_width_bits [model/core/platform_config.sail:157]
- **Spec evidence/anchor:** src/priv/machine.adoc:1546 [norm:mhpmcounter_sz]
## `HPM_COUNTER20_WIDTH`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/HPM_COUNTER20_WIDTH.yaml`
- **Sail match/evidence:** base.hpmcounter_width_bits → /properties/base/properties/hpmcounter_width_bits [model/core/platform_config.sail:157]
- **Spec evidence/anchor:** src/priv/machine.adoc:1546 [norm:mhpmcounter_sz]
## `HPM_COUNTER21_WIDTH`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/HPM_COUNTER21_WIDTH.yaml`
- **Sail match/evidence:** base.hpmcounter_width_bits → /properties/base/properties/hpmcounter_width_bits [model/core/platform_config.sail:157]
- **Spec evidence/anchor:** src/priv/machine.adoc:1546 [norm:mhpmcounter_sz]
## `HPM_COUNTER22_WIDTH`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/HPM_COUNTER22_WIDTH.yaml`
- **Sail match/evidence:** base.hpmcounter_width_bits → /properties/base/properties/hpmcounter_width_bits [model/core/platform_config.sail:157]
- **Spec evidence/anchor:** src/priv/machine.adoc:1546 [norm:mhpmcounter_sz]
## `HPM_COUNTER23_WIDTH`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/HPM_COUNTER23_WIDTH.yaml`
- **Sail match/evidence:** base.hpmcounter_width_bits → /properties/base/properties/hpmcounter_width_bits [model/core/platform_config.sail:157]
- **Spec evidence/anchor:** src/priv/machine.adoc:1546 [norm:mhpmcounter_sz]
## `HPM_COUNTER24_WIDTH`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/HPM_COUNTER24_WIDTH.yaml`
- **Sail match/evidence:** base.hpmcounter_width_bits → /properties/base/properties/hpmcounter_width_bits [model/core/platform_config.sail:157]
- **Spec evidence/anchor:** src/priv/machine.adoc:1546 [norm:mhpmcounter_sz]
## `HPM_COUNTER25_WIDTH`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/HPM_COUNTER25_WIDTH.yaml`
- **Sail match/evidence:** base.hpmcounter_width_bits → /properties/base/properties/hpmcounter_width_bits [model/core/platform_config.sail:157]
- **Spec evidence/anchor:** src/priv/machine.adoc:1546 [norm:mhpmcounter_sz]
## `HPM_COUNTER26_WIDTH`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/HPM_COUNTER26_WIDTH.yaml`
- **Sail match/evidence:** base.hpmcounter_width_bits → /properties/base/properties/hpmcounter_width_bits [model/core/platform_config.sail:157]
- **Spec evidence/anchor:** src/priv/machine.adoc:1546 [norm:mhpmcounter_sz]
## `HPM_COUNTER27_WIDTH`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/HPM_COUNTER27_WIDTH.yaml`
- **Sail match/evidence:** base.hpmcounter_width_bits → /properties/base/properties/hpmcounter_width_bits [model/core/platform_config.sail:157]
- **Spec evidence/anchor:** src/priv/machine.adoc:1546 [norm:mhpmcounter_sz]
## `HPM_COUNTER28_WIDTH`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/HPM_COUNTER28_WIDTH.yaml`
- **Sail match/evidence:** base.hpmcounter_width_bits → /properties/base/properties/hpmcounter_width_bits [model/core/platform_config.sail:157]
- **Spec evidence/anchor:** src/priv/machine.adoc:1546 [norm:mhpmcounter_sz]
## `HPM_COUNTER29_WIDTH`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/HPM_COUNTER29_WIDTH.yaml`
- **Sail match/evidence:** base.hpmcounter_width_bits → /properties/base/properties/hpmcounter_width_bits [model/core/platform_config.sail:157]
- **Spec evidence/anchor:** src/priv/machine.adoc:1546 [norm:mhpmcounter_sz]
## `HPM_COUNTER30_WIDTH`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/HPM_COUNTER30_WIDTH.yaml`
- **Sail match/evidence:** base.hpmcounter_width_bits → /properties/base/properties/hpmcounter_width_bits [model/core/platform_config.sail:157]
- **Spec evidence/anchor:** src/priv/machine.adoc:1546 [norm:mhpmcounter_sz]
## `HPM_COUNTER31_WIDTH`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/HPM_COUNTER31_WIDTH.yaml`
- **Sail match/evidence:** base.hpmcounter_width_bits → /properties/base/properties/hpmcounter_width_bits [model/core/platform_config.sail:157]
- **Spec evidence/anchor:** src/priv/machine.adoc:1546 [norm:mhpmcounter_sz]
## `HPM_COUNTER3_WIDTH`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/HPM_COUNTER3_WIDTH.yaml`
- **Sail match/evidence:** base.hpmcounter_width_bits → /properties/base/properties/hpmcounter_width_bits [model/core/platform_config.sail:157]
- **Spec evidence/anchor:** src/priv/machine.adoc:1546 [norm:mhpmcounter_sz]
## `HPM_COUNTER4_WIDTH`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/HPM_COUNTER4_WIDTH.yaml`
- **Sail match/evidence:** base.hpmcounter_width_bits → /properties/base/properties/hpmcounter_width_bits [model/core/platform_config.sail:157]
- **Spec evidence/anchor:** src/priv/machine.adoc:1546 [norm:mhpmcounter_sz]
## `HPM_COUNTER5_WIDTH`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/HPM_COUNTER5_WIDTH.yaml`
- **Sail match/evidence:** base.hpmcounter_width_bits → /properties/base/properties/hpmcounter_width_bits [model/core/platform_config.sail:157]
- **Spec evidence/anchor:** src/priv/machine.adoc:1546 [norm:mhpmcounter_sz]
## `HPM_COUNTER6_WIDTH`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/HPM_COUNTER6_WIDTH.yaml`
- **Sail match/evidence:** base.hpmcounter_width_bits → /properties/base/properties/hpmcounter_width_bits [model/core/platform_config.sail:157]
- **Spec evidence/anchor:** src/priv/machine.adoc:1546 [norm:mhpmcounter_sz]
## `HPM_COUNTER7_WIDTH`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/HPM_COUNTER7_WIDTH.yaml`
- **Sail match/evidence:** base.hpmcounter_width_bits → /properties/base/properties/hpmcounter_width_bits [model/core/platform_config.sail:157]
- **Spec evidence/anchor:** src/priv/machine.adoc:1546 [norm:mhpmcounter_sz]
## `HPM_COUNTER8_WIDTH`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/HPM_COUNTER8_WIDTH.yaml`
- **Sail match/evidence:** base.hpmcounter_width_bits → /properties/base/properties/hpmcounter_width_bits [model/core/platform_config.sail:157]
- **Spec evidence/anchor:** src/priv/machine.adoc:1546 [norm:mhpmcounter_sz]
## `HPM_COUNTER9_WIDTH`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/HPM_COUNTER9_WIDTH.yaml`
- **Sail match/evidence:** base.hpmcounter_width_bits → /properties/base/properties/hpmcounter_width_bits [model/core/platform_config.sail:157]
- **Spec evidence/anchor:** src/priv/machine.adoc:1546 [norm:mhpmcounter_sz]
## `HPM_COUNTER_EN`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/HPM_COUNTER_EN.yaml`
- **Sail match/evidence:** base.writable_hpm_counters → /properties/base/properties/writable_hpm_counters [model/core/sys_regs.sail:123]
- **Spec evidence/anchor:** src/priv/machine.adoc:1540 [norm:mhpmcounter_mhpmevent_rdonly0]
## `HPM_EVENTS`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/HPM_EVENTS.yaml`
- **Sail match/evidence:** platform.event_selectors → /properties/platform/properties/event_selectors [model/core/events.sail:50]
- **Spec evidence/anchor:** src/priv/machine.adoc:1537 [norm:mhpmevent_enc]
## `HSTATEEN0_FCSR_TYPE`
- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/HSTATEEN0_FCSR_TYPE.yaml`
- **Sail identity:** `extensions.Stateen.hstateen0.FCSR`; hierarchy level `extensions.Stateen.hstateen0`
- **Schema:** `/properties/extensions/properties/Stateen/properties/hstateen0/properties/FCSR`; type `string`; definition `{"description":"core/platform_config.sail:140.39-140.79","enum":["CSRBit_ReadOnlyOne","CSRBit_ReadOnlyZero","CSRBit_Writable"],"type":"string"}`
- **Sail source evidence:** `model/core/platform_config.sail:140-140`
- **Spec mention / defining-location candidate:** `src/priv/smstateen.adoc:251` (extension and setting terms); no normative anchor confidently identified.
- **Defining status:** Spec mention found; first defining location remains unresolved.
- **UDB match:** Semantic match to Sail `extensions.Stateen.hstateen0.FCSR`; UDB `name`, `long_name`, and definition agree with the setting's behavior.
## `HSTATEEN_CONTEXT_TYPE`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/HSTATEEN_CONTEXT_TYPE.yaml`
- **Sail match/evidence:** extensions.Stateen.hstateen0.CONTEXT → /properties/extensions/properties/Stateen/properties/hstateen0/properties/CONTEXT [model/core/platform_config.sail:139]
- **Spec evidence/anchor:** src/priv/smstateen.adoc:301 [norm:hstateen0_context_op]
## `HSTATEEN_CSRIND_TYPE`

- **Class:** `0b111`
- **Sail schema pointer:** `/properties/extensions/properties/Stateen/properties/hstateen0/properties/CSRIND`; Sail identity `extensions.Stateen.hstateen0.CSRIND` (`model/core/platform_config.sail:142`).
- **UDB YAML:** `spec/std/isa/param/HSTATEEN_CSRIND_TYPE.yaml`
- **Sail match/evidence:** `extensions.Stateen.hstateen0.CSRIND` (`CSRBitConfig`: `CSRBit_Writable` / `CSRBit_ReadOnlyZero` / `CSRBit_ReadOnlyOne` maps to UDB `rw` / `read-only-0` / `read-only-1`; model/core/platform_config.sail:112-125,142; model/extensions/Stateen/stateen_regs.sail:133-139; config/config.json.in:1302-1308). Present in the rebuilt schema at `/properties/extensions/properties/Stateen/properties/hstateen0/properties/CSRIND`.
- **Spec evidence/anchor:** src/priv/smstateen.adoc:279 [norm:hstateen0_csrind_op]
## `HSTATEEN_ENVCFG_TYPE`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/HSTATEEN_ENVCFG_TYPE.yaml`
- **Sail match/evidence:** extensions.Stateen.hstateen0.ENVCFG → /properties/extensions/properties/Stateen/properties/hstateen0/properties/ENVCFG [model/core/platform_config.sail:138]
- **Spec evidence/anchor:** src/priv/smstateen.adoc:274 [norm:hstateen0_envcfg_op]
## `HW_MSTATUS_FS_DIRTY_UPDATE`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/HW_MSTATUS_FS_DIRTY_UPDATE.yaml`
- **Sail match/evidence:** base.mstatus (fixed dirty-state behavior) [model/core/sys_regs.sail:86]
- **Spec evidence/anchor:** src/priv/machine.adoc:950 [norm:mstatus_fs_imprecise]
## `HW_MSTATUS_VS_DIRTY_UPDATE`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/HW_MSTATUS_VS_DIRTY_UPDATE.yaml`
- **Sail match/evidence:** base.mstatus (fixed dirty-state behavior) [model/core/sys_regs.sail:86]
- **Spec evidence/anchor:** src/priv/machine.adoc:973 [norm:mstatus_vs_imprecise]
## `IGNORE_INVALID_VSATP_MODE_WRITES_WHEN_V_EQ_ZERO`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/IGNORE_INVALID_VSATP_MODE_WRITES_WHEN_V_EQ_ZERO.yaml`
- **Sail match/evidence:** extensions.H.vsatp_modes → /properties/extensions/properties/H/properties/vsatp_modes [model/core/platform_config.sail:44]
- **Spec evidence/anchor:** src/priv/hypervisor.adoc:1416 [norm:vsatp_mode_unsupported_v0]
## `IMP_ID_VALUE`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/IMP_ID_VALUE.yaml`
- **Sail match/evidence:** platform.impid → /properties/platform/properties/impid [model/core/sys_regs.sail:878]
- **Spec evidence/anchor:** src/priv/machine.adoc:289 [norm:mimpid_op]
## `LEGAL_VSTART`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/LEGAL_VSTART.yaml`
- **Sail match/evidence:** extensions.V.vstart → /properties/extensions/properties/V/properties/vstart [model/extensions/V/vext_arith_insts.sail:78]
- **Spec evidence/anchor:** src/unpriv/vector-common.adoc:552 [norm:vstart_sz_writable]
## `LRSC_FAIL_ON_NON_EXACT_LRSC`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/LRSC_FAIL_ON_NON_EXACT_LRSC.yaml`
- **Sail match/evidence:** platform.reservation.require_exact_reservation_addr → /properties/platform/properties/reservation/properties/require_exact_reservation_addr [model/core/platform_config.sail:70]
- **Spec evidence/anchor:** src/unpriv/zalrsc.adoc:204 [norm:lrsc_same_address_and_size]
## `LRSC_MISALIGNED_BEHAVIOR`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/LRSC_MISALIGNED_BEHAVIOR.yaml`
- **Sail match/evidence:** memory.misaligned.exceptions.lrsc → /properties/memory/properties/misaligned/properties/exceptions/allOf/0/properties/lrsc [model/core/platform_config.sail:103]
- **Spec evidence/anchor:** src/unpriv/zalrsc.adoc:74 [norm:lr_sc_alignment]
## `LRSC_RESERVATION_STRATEGY`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/LRSC_RESERVATION_STRATEGY.yaml`
- **Sail match/evidence:** platform.reservation.reservation_set_size_exp → /properties/platform/properties/reservation/properties/reservation_set_size_exp [model/core/platform_config.sail:62]
- **Spec evidence/anchor:** src/unpriv/zalrsc.adoc:91 [norm:lr_reservation_set_size]
## `M_MODE_ENDIANNESS`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/M_MODE_ENDIANNESS.yaml`
- **Sail match/evidence:** `mstatus.MBE` field; model fixes MBE to little-endian behavior [model/core/sys_regs.sail:215] [model/sys/sys_control.sail:558]
- **Spec evidence/anchor:** src/priv/machine.adoc:644 [norm:mstatus_mbe_op]
## `MARCHID_IMPLEMENTED`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/MARCHID_IMPLEMENTED.yaml`
- **Sail match/evidence:** platform.archid → /properties/platform/properties/archid [model/core/sys_regs.sail:879]
- **Spec evidence/anchor:** src/priv/machine.adoc:253 [norm:marchid_always_rd]
## `MCID_WIDTH`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/MCID_WIDTH.yaml`
- **Sail match/evidence:** extensions.Ssqosid.mcid_length → /properties/extensions/properties/Ssqosid/properties/mcid_length [model/extensions/Ssqosid/ssqosid.sail:10]
- **Spec evidence/anchor:** src/priv/ssqosid.adoc:45 [norm:Ssqosid_srmcfg_register_size]
## `MCONTEXT_IMPLEMENTED`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/MCONTEXT_IMPLEMENTED.yaml`
- **Sail match/evidence:** extensions.Sdtrig.mcontext.supported → /properties/extensions/properties/Sdtrig/properties/mcontext/properties/supported [model/core/platform_config.sail:15]
- **Spec evidence/anchor:** src/priv/csrs.adoc:513 [CSR list]
## `MCOUNTENABLE_EN`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/MCOUNTENABLE_EN.yaml`
- **Sail match/evidence:** base.mcounteren_writable_bits → /properties/base/properties/mcounteren_writable_bits [model/core/sys_regs.sail:828]
- **Spec evidence/anchor:** src/priv/machine.adoc:1558 [norm:mcounteren_op]
## `MCOUNTINHIBIT_IMPLEMENTED`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/MCOUNTINHIBIT_IMPLEMENTED.yaml`
- **Sail match/evidence:** base.mcountinhibit.supported → /properties/base/properties/mcountinhibit/properties/supported [model/core/platform_config.sail:15]
- **Spec evidence/anchor:** src/priv/machine.adoc:1638 [norm:mcountinhibit_not_impl]
## `MEDELEG_DELEGATABLE`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/MEDELEG_DELEGATABLE.yaml`
- **Sail match/evidence:** base.medeleg.delegatable_bits → /properties/base/properties/medeleg/properties/delegatable_bits [model/core/platform_config.sail:36]
- **Spec evidence/anchor:** src/priv/machine.adoc:1263 [norm:medeleg_mideleg_warl]
## `MEI_INTR_IMPL`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/MEI_INTR_IMPL.yaml`
- **Sail match/evidence:** platform.interrupts.machine.external.supported → /properties/platform/properties/interrupts/properties/machine/properties/external/properties/supported [model/core/platform_config.sail:195]
- **Spec evidence/anchor:** src/priv/machine.adoc:1379 [norm:mip_std_enc_img]
## `MIDELEG_DELEGATABLE`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/MIDELEG_DELEGATABLE.yaml`
- **Sail match/evidence:** base.mideleg.delegatable_bits → /properties/base/properties/mideleg/properties/delegatable_bits [model/core/platform_config.sail:36]
- **Spec evidence/anchor:** src/priv/machine.adoc:1263 [norm:medeleg_mideleg_warl]
## `MIMPID_IMPLEMENTED`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/MIMPID_IMPLEMENTED.yaml`
- **Sail match/evidence:** platform.impid → /properties/platform/properties/impid [model/core/sys_regs.sail:878]
- **Spec evidence/anchor:** src/priv/machine.adoc:291 [norm:mimpid_always_rd]
## `MISA_CSR_IMPLEMENTED`

- **Class:** `0b111`
- **Sail schema pointer:** `/properties/base/properties/misa/properties/implemented`; Sail identity `base.misa.implemented` (`model/core/platform_config.sail:12`).
- **UDB YAML:** `spec/std/isa/param/MISA_CSR_IMPLEMENTED.yaml`
- **Sail match/evidence:** base.misa.implemented → /properties/base/properties/misa/properties/implemented [model/core/platform_config.sail:12]
- **Spec evidence/anchor:** src/priv/machine.adoc:23 [norm:misa_csr_implemented]
## `MISALIGNED_AMO`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/MISALIGNED_AMO.yaml`
- **Sail match/evidence:** memory.misaligned.exceptions.amo → /properties/memory/properties/misaligned/properties/exceptions/allOf/0/properties/amo [model/core/platform_config.sail:102]
- **Spec evidence/anchor:** src/priv/machine.adoc:3096 [norm:pma_mag_op_amo]
## `MISALIGNED_LDST`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/MISALIGNED_LDST.yaml`
- **Sail match/evidence:** memory.misaligned.exceptions.load_store → /properties/memory/properties/misaligned/properties/exceptions/allOf/0/properties/load_store [model/core/platform_config.sail:100]
- **Spec evidence/anchor:** src/unpriv/rv32.adoc:706 [norm:misaligned_ldst_hw_support]
## `MISALIGNED_LDST_EXCEPTION_PRIORITY`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/MISALIGNED_LDST_EXCEPTION_PRIORITY.yaml`
- **Sail match/evidence:** fixed.misaligned_exception_priority [model/sys/mem.sail:228]
- **Spec evidence/anchor:** src/priv/machine.adoc:1932 [norm:mcause_exccode_pri2]
## `MISALIGNED_MAX_ATOMICITY_GRANULE_SIZE`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/MISALIGNED_MAX_ATOMICITY_GRANULE_SIZE.yaml`
- **Sail match/evidence:** memory.regions.attributes.misaligned_atomicity_granule_size_exp [model/sys/pma.sail:205]
- **Spec evidence/anchor:** src/unpriv/zaamo.adoc:25 [norm:misaligned_atomicity_granule_size]
## `MISALIGNED_SPLIT_STRATEGY`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/MISALIGNED_SPLIT_STRATEGY.yaml`
- **Sail match/evidence:** memory.misaligned → /properties/memory/properties/misaligned [model/sys/split_access_utils.sail:9]
- **Spec evidence/anchor:** src/unpriv/rvwmo.adoc:92 [norm:rvwmo_misaligned_ldst_memops]
## `MSI_INTR_IMPL`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/MSI_INTR_IMPL.yaml`
- **Sail match/evidence:** platform.interrupts.machine.software.supported → /properties/platform/properties/interrupts/properties/machine/properties/software/properties/supported [model/core/platform_config.sail:193]
- **Spec evidence/anchor:** src/priv/machine.adoc:1379 [norm:mip_std_enc_img]
## `MSTATEEN0_FCSR_TYPE`
- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/MSTATEEN0_FCSR_TYPE.yaml`
- **Sail identity:** `extensions.Stateen.mstateen0.FCSR`; hierarchy level `extensions.Stateen.mstateen0`
- **Schema:** `/properties/extensions/properties/Stateen/properties/mstateen0/properties/FCSR`; type `string`; definition `{"description":"core/platform_config.sail:131.39-131.79","enum":["CSRBit_ReadOnlyOne","CSRBit_ReadOnlyZero","CSRBit_Writable"],"type":"string"}`
- **Sail source evidence:** `model/core/platform_config.sail:131-131`
- **Spec mention / defining-location candidate:** `src/priv/smstateen.adoc:251` (extension and setting terms); no normative anchor confidently identified.
- **Defining status:** Spec mention found; first defining location remains unresolved.
- **UDB match:** Semantic match to Sail `extensions.Stateen.mstateen0.FCSR`; UDB `name`, `long_name`, and definition agree with the setting's behavior.
## `MSTATEEN0_SE0_TYPE`
- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/MSTATEEN0_SE0_TYPE.yaml`
- **Sail identity:** `extensions.Stateen.mstateen0.SE0`; hierarchy level `extensions.Stateen.mstateen0`
- **Schema:** `/properties/extensions/properties/Stateen/properties/mstateen0/properties/SE0`; type `string`; definition `{"description":"core/platform_config.sail:126.39-126.78","enum":["CSRBit_ReadOnlyOne","CSRBit_ReadOnlyZero","CSRBit_Writable"],"type":"string"}`
- **Sail source evidence:** `model/core/platform_config.sail:126-126`
- **Spec mention / defining-location candidate:** `src/priv/smstateen.adoc:263` (extension and setting terms); no normative anchor confidently identified.
- **Defining status:** Spec mention found; first defining location remains unresolved.
- **UDB match:** Semantic match to Sail `extensions.Stateen.mstateen0.SE0`; UDB `name`, `long_name`, and definition agree with the setting's behavior.
## `MSTATEEN1_SE0_TYPE`
- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/MSTATEEN1_SE0_TYPE.yaml`
- **Sail identity:** `extensions.Stateen.mstateen1.SE1`; hierarchy level `extensions.Stateen.mstateen1`
- **Schema:** `/properties/extensions/properties/Stateen/properties/mstateen1/properties/SE1`; type `string`; definition `{"description":"core/platform_config.sail:134.39-134.78","enum":["CSRBit_ReadOnlyOne","CSRBit_ReadOnlyZero","CSRBit_Writable"],"type":"string"}`
- **Sail source evidence:** `model/core/platform_config.sail:134-134`
- **Spec evidence/anchor:** `src/priv/smstateen.adoc:162-166` [`norm:mstateen_bit_63_op`] states bit 63 in each `mstateen` CSR controls access to the matching `sstateen` and `hstateen` banks.
- **Defining status:** Normative rule anchor found for matching-bank access control; it does not spell out the model's full writable/read-only choice.
- **UDB match:** Semantic match to Sail `extensions.Stateen.mstateen1.SE1`; UDB `name`, `long_name`, and definition agree with the setting's behavior.
- **Identifier discrepancy:** UDB labels this control SE0; Sail labels bit 63 SE1. Sail's register definition and the manual's `norm:mstateen_bit_63_op` both identify the bit as controlling the matching `stateen1` banks. Kept as a semantic match with this caveat. The same normative rule is the basis for setting the spec-presence bit.
## `MSTATEEN2_SE0_TYPE`
- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/MSTATEEN2_SE0_TYPE.yaml`
- **Sail identity:** `extensions.Stateen.mstateen2.SE2`; hierarchy level `extensions.Stateen.mstateen2`
- **Schema:** `/properties/extensions/properties/Stateen/properties/mstateen2/properties/SE2`; type `string`; definition `{"description":"core/platform_config.sail:135.39-135.78","enum":["CSRBit_ReadOnlyOne","CSRBit_ReadOnlyZero","CSRBit_Writable"],"type":"string"}`
- **Sail source evidence:** `model/core/platform_config.sail:135-135`
- **Spec evidence/anchor:** `src/priv/smstateen.adoc:162-166` [`norm:mstateen_bit_63_op`] states bit 63 in each `mstateen` CSR controls access to the matching `sstateen` and `hstateen` banks.
- **Defining status:** Normative rule anchor found for matching-bank access control; it does not spell out the model's full writable/read-only choice.
- **UDB match:** Semantic match to Sail `extensions.Stateen.mstateen2.SE2`; UDB `name`, `long_name`, and definition agree with the setting's behavior.
- **Identifier discrepancy:** UDB labels this control SE0; Sail labels bit 63 SE2. Sail's register definition and the manual's `norm:mstateen_bit_63_op` both identify the bit as controlling the matching `stateen2` banks. Kept as a semantic match with this caveat. The same normative rule is the basis for setting the spec-presence bit.
## `MSTATEEN3_SE0_TYPE`
- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/MSTATEEN3_SE0_TYPE.yaml`
- **Sail identity:** `extensions.Stateen.mstateen3.SE3`; hierarchy level `extensions.Stateen.mstateen3`
- **Schema:** `/properties/extensions/properties/Stateen/properties/mstateen3/properties/SE3`; type `string`; definition `{"description":"core/platform_config.sail:136.39-136.78","enum":["CSRBit_ReadOnlyOne","CSRBit_ReadOnlyZero","CSRBit_Writable"],"type":"string"}`
- **Sail source evidence:** `model/core/platform_config.sail:136-136`
- **Spec evidence/anchor:** `src/priv/smstateen.adoc:162-166` [`norm:mstateen_bit_63_op`] states bit 63 in each `mstateen` CSR controls access to the matching `sstateen` and `hstateen` banks.
- **Defining status:** Normative rule anchor found for matching-bank access control; it does not spell out the model's full writable/read-only choice.
- **UDB match:** Semantic match to Sail `extensions.Stateen.mstateen3.SE3`; UDB `name`, `long_name`, and definition agree with the setting's behavior.
- **Identifier discrepancy:** UDB labels this control SE0; Sail labels bit 63 SE3. Sail's register definition and the manual's `norm:mstateen_bit_63_op` both identify the bit as controlling the matching `stateen3` banks. Kept as a semantic match with this caveat. The same normative rule is the basis for setting the spec-presence bit.
## `MSTATEEN_CONTEXT_TYPE`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/MSTATEEN_CONTEXT_TYPE.yaml`
- **Sail match/evidence:** extensions.Stateen.mstateen0.CONTEXT → /properties/extensions/properties/Stateen/properties/mstateen0/properties/CONTEXT [model/core/platform_config.sail:128]
- **Spec evidence/anchor:** src/priv/smstateen.adoc:300 [norm:mstateen0_context_op]
## `MSTATEEN_CSRIND_TYPE`

- **Class:** `0b111`
- **Sail schema pointer:** `/properties/extensions/properties/Stateen/properties/mstateen0/properties/CSRIND`; Sail identity `extensions.Stateen.mstateen0.CSRIND` (`model/core/platform_config.sail:130`).
- **UDB YAML:** `spec/std/isa/param/MSTATEEN_CSRIND_TYPE.yaml`
- **Sail match/evidence:** `extensions.Stateen.mstateen0.CSRIND` (`CSRBitConfig`: `CSRBit_Writable` / `CSRBit_ReadOnlyZero` / `CSRBit_ReadOnlyOne` maps to UDB `rw` / `read-only-0` / `read-only-1`; model/core/platform_config.sail:112-125,130; model/extensions/Stateen/stateen_regs.sail:57-64; config/config.json.in:1281-1289). Present in the rebuilt schema at `/properties/extensions/properties/Stateen/properties/mstateen0/properties/CSRIND`.
- **Spec evidence/anchor:** src/priv/smstateen.adoc:277 [norm:mstateen0_csrind_op]
## `MSTATEEN_ENVCFG_TYPE`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/MSTATEEN_ENVCFG_TYPE.yaml`
- **Sail match/evidence:** extensions.Stateen.mstateen0.ENVCFG → /properties/extensions/properties/Stateen/properties/mstateen0/properties/ENVCFG [model/core/platform_config.sail:127]
- **Spec evidence/anchor:** src/priv/smstateen.adoc:273 [norm:mstateen0_envcfg_op]
## `MSTATUS_FS_LEGAL_VALUES`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/MSTATUS_FS_LEGAL_VALUES.yaml`
- **Sail match/evidence:** base.mstatus.fs_legal_states → /properties/base/properties/mstatus/properties/fs_legal_states [model/core/platform_config.sail:153]
- **Spec evidence/anchor:** src/priv/machine.adoc:845 [norm:mstatus_fs_acc1]
## `MSTATUS_VS_LEGAL_VALUES`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/MSTATUS_VS_LEGAL_VALUES.yaml`
- **Sail match/evidence:** base.mstatus.vs_legal_states → /properties/base/properties/mstatus/properties/vs_legal_states [model/core/platform_config.sail:154]
- **Spec evidence/anchor:** src/priv/machine.adoc:861 [norm:mstatus_vs_acc1]
## `MTI_INTR_IMPL`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/MTI_INTR_IMPL.yaml`
- **Sail match/evidence:** platform.interrupts.machine.timer.supported → /properties/platform/properties/interrupts/properties/machine/properties/timer/properties/supported [model/core/platform_config.sail:194]
- **Spec evidence/anchor:** src/priv/machine.adoc:1379 [norm:mip_std_enc_img]
## `MTVAL_WIDTH`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/MTVAL_WIDTH.yaml`
- **Sail match/evidence:** xlenbits trap information is written to `mtval` [model/sys/sys_control.sail:308]
- **Spec evidence/anchor:** src/priv/machine.adoc:2020 [norm:mtval_enc_img]
## `MTVEC_ACCESS`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/MTVEC_ACCESS.yaml`
- **Sail match/evidence:** base.mtvec.direct → /properties/base/properties/mtvec/properties/direct [model/core/platform_config.sail:3]
- **Spec evidence/anchor:** src/priv/machine.adoc:1174 [norm:mtvec_rdonly]
## `MTVEC_BASE_ALIGNMENT_DIRECT`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/MTVEC_BASE_ALIGNMENT_DIRECT.yaml`
- **Sail match/evidence:** base.mtvec.direct → /properties/base/properties/mtvec/properties/direct [model/core/platform_config.sail:3]
- **Spec evidence/anchor:** src/priv/machine.adoc:1177 [norm:mtvec_base_align_4B]
## `MTVEC_BASE_ALIGNMENT_VECTORED`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/MTVEC_BASE_ALIGNMENT_VECTORED.yaml`
- **Sail match/evidence:** base.mtvec.vectored → /properties/base/properties/mtvec/properties/vectored [model/core/platform_config.sail:20]
- **Spec evidence/anchor:** src/priv/machine.adoc:1179 [norm:mtvec_base_align_func_mode]
## `MTVEC_ILLEGAL_WRITE_BEHAVIOR`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/MTVEC_ILLEGAL_WRITE_BEHAVIOR.yaml`
- **Sail match/evidence:** base.mtvec.direct → /properties/base/properties/mtvec/properties/direct [model/core/platform_config.sail:3]
- **Spec evidence/anchor:** src/priv/machine.adoc:1165 [norm:mtvec_sz_warl_acc]
## `MTVEC_MODES`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/MTVEC_MODES.yaml`
- **Sail match/evidence:** base.mtvec.vectored → /properties/base/properties/mtvec/properties/vectored [model/core/platform_config.sail:20]
- **Spec evidence/anchor:** src/priv/machine.adoc:1204 [norm:mtvec_mode_direct_op]
## `MUTABLE_MISA_A`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/MUTABLE_MISA_A.yaml`
- **Sail match/evidence:** extensions.A.mutable_misa → /properties/extensions/properties/A/properties/mutable_misa [model/core/sys_regs.sail:137]
- **Spec evidence/anchor:** src/priv/machine.adoc:73 [norm:misa_extensions_disabling]
## `MUTABLE_MISA_B`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/MUTABLE_MISA_B.yaml`
- **Sail match/evidence:** extensions.B.mutable_misa → /properties/extensions/properties/B/properties/mutable_misa [model/core/sys_regs.sail:137]
- **Spec evidence/anchor:** src/priv/machine.adoc:73 [norm:misa_extensions_disabling]
## `MUTABLE_MISA_C`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/MUTABLE_MISA_C.yaml`
- **Sail match/evidence:** extensions.C.mutable_misa → /properties/extensions/properties/C/properties/mutable_misa [model/core/sys_regs.sail:137]
- **Spec evidence/anchor:** src/priv/machine.adoc:73 [norm:misa_extensions_disabling]
## `MUTABLE_MISA_D`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/MUTABLE_MISA_D.yaml`
- **Sail match/evidence:** extensions.D.mutable_misa → /properties/extensions/properties/D/properties/mutable_misa [model/core/sys_regs.sail:137]
- **Spec evidence/anchor:** src/priv/machine.adoc:73 [norm:misa_extensions_disabling]
## `MUTABLE_MISA_F`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/MUTABLE_MISA_F.yaml`
- **Sail match/evidence:** extensions.F.mutable_misa → /properties/extensions/properties/F/properties/mutable_misa [model/core/sys_regs.sail:137]
- **Spec evidence/anchor:** src/priv/machine.adoc:73 [norm:misa_extensions_disabling]
## `MUTABLE_MISA_H`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/MUTABLE_MISA_H.yaml`
- **Sail match/evidence:** extensions.H.mutable_misa → /properties/extensions/properties/H/properties/mutable_misa [model/core/sys_regs.sail:137]
- **Spec evidence/anchor:** src/priv/machine.adoc:73 [norm:misa_extensions_disabling]
## `MUTABLE_MISA_M`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/MUTABLE_MISA_M.yaml`
- **Sail match/evidence:** extensions.M.mutable_misa → /properties/extensions/properties/M/properties/mutable_misa [model/core/sys_regs.sail:137]
- **Spec evidence/anchor:** src/priv/machine.adoc:73 [norm:misa_extensions_disabling]
## `MUTABLE_MISA_S`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/MUTABLE_MISA_S.yaml`
- **Sail match/evidence:** extensions.S.mutable_misa → /properties/extensions/properties/S/properties/mutable_misa [model/core/sys_regs.sail:137]
- **Spec evidence/anchor:** src/priv/machine.adoc:73 [norm:misa_extensions_disabling]
## `MUTABLE_MISA_U`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/MUTABLE_MISA_U.yaml`
- **Sail match/evidence:** extensions.U.mutable_misa → /properties/extensions/properties/U/properties/mutable_misa [model/core/sys_regs.sail:137]
- **Spec evidence/anchor:** src/priv/machine.adoc:73 [norm:misa_extensions_disabling]
## `MUTABLE_MISA_V`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/MUTABLE_MISA_V.yaml`
- **Sail match/evidence:** extensions.V.mutable_misa → /properties/extensions/properties/V/properties/mutable_misa [model/core/sys_regs.sail:137]
- **Spec evidence/anchor:** src/priv/machine.adoc:73 [norm:misa_extensions_disabling]
## `MXLEN`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/MXLEN.yaml`
- **Sail match/evidence:** base.xlen → /properties/base/properties/xlen [model/core/xlen.sail:9]
- **Spec evidence/anchor:** src/priv/machine.adoc:29 [norm:misa_mxl_op_isa]
## `NON_STANDARD_EXTENSION_IMPLEMENTED`

- **Class:** `0b111`
- **Sail schema pointer:** `/properties/base/properties/misa/properties/has_non_standard_extensions`; Sail identity `base.misa.has_non_standard_extensions` (`model/core/platform_config.sail:14`).
- **UDB YAML:** `spec/std/isa/param/NON_STANDARD_EXTENSION_IMPLEMENTED.yaml`
- **Sail match/evidence:** `base.misa.has_non_standard_extensions` (boolean; model/core/platform_config.sail:14; config/config.json.in:27), consumed to set `misa.X` (model/sys/sys_control.sail:529-530). Present in the rebuilt schema at `/properties/base/properties/misa/properties/has_non_standard_extensions`.
- **Spec evidence/anchor:** src/priv/machine.adoc:142 [norm:misa_x_op]
## `NUM_EXTERNAL_GUEST_INTERRUPTS`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/NUM_EXTERNAL_GUEST_INTERRUPTS.yaml`
- **Sail match/evidence:** extensions.H.geilen → /properties/extensions/properties/H/properties/geilen [model/core/platform_config.sail:44]
- **Spec evidence/anchor:** src/priv/hypervisor.adoc:634 [norm:geilen]
## `NUM_PMP_ENTRIES`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/NUM_PMP_ENTRIES.yaml`
- **Sail match/evidence:** memory.pmp.count → /properties/memory/properties/pmp/properties/count [model/pmp/pmp_regs.sail:12]
- **Spec evidence/anchor:** src/priv/machine.adoc:3341 [norm:pmp_entry_count]
## `NUM_USABLE_PMP_ENTRIES`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/NUM_USABLE_PMP_ENTRIES.yaml`
- **Sail match/evidence:** memory.pmp.usable_count → /properties/memory/properties/pmp/properties/usable_count [model/pmp/pmp_regs.sail:17]
- **Spec evidence/anchor:** src/priv/machine.adoc:3341 [norm:pmp_entry_count]
## `PHYS_ADDR_WIDTH`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/PHYS_ADDR_WIDTH.yaml`
- **Sail match/evidence:** memory.physaddr_bits → /properties/memory/properties/physaddr_bits [model/core/mem_addrtype.sail:31]
- **Spec evidence/anchor:** src/priv/supervisor.adoc:1473 [physical address bits]
## `PMA_GRANULARITY`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/PMA_GRANULARITY.yaml`
- **Sail match/evidence:** memory.regions → /properties/memory/properties/regions [model/sys/pma.sail:327] [partial: region/PMA representation]
- **Spec evidence/anchor:** src/priv/machine.adoc:3078 [norm:pma_mag_def]
## `PMP_GRANULARITY`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/PMP_GRANULARITY.yaml`
- **Sail match/evidence:** memory.pmp.grain → /properties/memory/properties/pmp/properties/grain [model/pmp/pmp_regs.sail:21]
- **Spec evidence/anchor:** src/priv/machine.adoc:3310 [norm:pmp_granularity]
## `PMP_NA4_SUPPORTED`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/PMP_NA4_SUPPORTED.yaml`
- **Sail match/evidence:** memory.pmp.na4_supported → /properties/memory/properties/pmp/properties/na4_supported [model/pmp/pmp_regs.sail:123]
- **Spec evidence/anchor:** src/priv/machine.adoc:3517 [norm:pmp_na4_select_restriction]
## `PMP_NAPOT_SUPPORTED`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/PMP_NAPOT_SUPPORTED.yaml`
- **Sail match/evidence:** memory.pmp.napot_supported → /properties/memory/properties/pmp/properties/napot_supported [model/pmp/pmp_regs.sail:124]
- **Spec evidence/anchor:** src/priv/machine.adoc:3428 [norm:pmp_a_field_napot_na4]
## `PMP_TOR_SUPPORTED`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/PMP_TOR_SUPPORTED.yaml`
- **Sail match/evidence:** memory.pmp.tor_supported → /properties/memory/properties/pmp/properties/tor_supported [model/pmp/pmp_regs.sail:121]
- **Spec evidence/anchor:** src/priv/machine.adoc:3491 [norm:pmp_a_field_tor]
## `PRECISE_SYNCHRONOUS_EXCEPTIONS`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/PRECISE_SYNCHRONOUS_EXCEPTIONS.yaml`
- **Sail match/evidence:** synchronous exception contexts and fixed trap path; coarse fixed-behavior match [model/exceptions/sync_exception.sail:9] [model/sys/sys_control.sail:268]
- **Spec evidence/anchor:** src/unpriv/intro.adoc:658 [EEI trap precision]
## `RCID_WIDTH`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/RCID_WIDTH.yaml`
- **Sail match/evidence:** extensions.Ssqosid.rcid_length → /properties/extensions/properties/Ssqosid/properties/rcid_length [model/extensions/Ssqosid/ssqosid.sail:9]
- **Spec evidence/anchor:** src/priv/ssqosid.adoc:45 [norm:Ssqosid_srmcfg_register_size]
## `REPORT_CAUSE_IN_MTVAL_ON_LANDING_PAD_SOFTWARE_CHECK`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/REPORT_CAUSE_IN_MTVAL_ON_LANDING_PAD_SOFTWARE_CHECK.yaml`
- **Sail match/evidence:** base.xtval_nonzero → /properties/base/properties/xtval_nonzero [model/core/platform_config.sail:201]
- **Spec evidence/anchor:** src/priv/machine.adoc:2076 [norm:mtval_swchk_list]
## `REPORT_CAUSE_IN_MTVAL_ON_SHADOW_STACK_SOFTWARE_CHECK`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/REPORT_CAUSE_IN_MTVAL_ON_SHADOW_STACK_SOFTWARE_CHECK.yaml`
- **Sail match/evidence:** base.xtval_nonzero → /properties/base/properties/xtval_nonzero [model/core/platform_config.sail:201]
- **Spec evidence/anchor:** src/priv/machine.adoc:2076 [norm:mtval_swchk_list]
## `REPORT_CAUSE_IN_STVAL_ON_LANDING_PAD_SOFTWARE_CHECK`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/REPORT_CAUSE_IN_STVAL_ON_LANDING_PAD_SOFTWARE_CHECK.yaml`
- **Sail match/evidence:** base.xtval_nonzero → /properties/base/properties/xtval_nonzero [model/core/platform_config.sail:201]
- **Spec evidence/anchor:** src/priv/sstvala.adoc:4 [norm:sstvala_stval_faulting_vaddr]
## `REPORT_CAUSE_IN_STVAL_ON_SHADOW_STACK_SOFTWARE_CHECK`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/REPORT_CAUSE_IN_STVAL_ON_SHADOW_STACK_SOFTWARE_CHECK.yaml`
- **Sail match/evidence:** base.xtval_nonzero → /properties/base/properties/xtval_nonzero [model/core/platform_config.sail:201]
- **Spec evidence/anchor:** src/priv/sstvala.adoc:4 [norm:sstvala_stval_faulting_vaddr]
## `REPORT_CAUSE_IN_VSTVAL_ON_LANDING_PAD_SOFTWARE_CHECK`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/REPORT_CAUSE_IN_VSTVAL_ON_LANDING_PAD_SOFTWARE_CHECK.yaml`
- **Sail match/evidence:** base.xtval_nonzero → /properties/base/properties/xtval_nonzero [model/core/platform_config.sail:201]
- **Spec evidence/anchor:** src/priv/shvstvala.adoc:4 [norm:shvstvala_vstval_written]
## `REPORT_CAUSE_IN_VSTVAL_ON_SHADOW_STACK_SOFTWARE_CHECK`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/REPORT_CAUSE_IN_VSTVAL_ON_SHADOW_STACK_SOFTWARE_CHECK.yaml`
- **Sail match/evidence:** base.xtval_nonzero → /properties/base/properties/xtval_nonzero [model/core/platform_config.sail:201]
- **Spec evidence/anchor:** src/priv/shvstvala.adoc:4 [norm:shvstvala_vstval_written]
## `REPORT_ENCODING_IN_MTVAL_ON_ILLEGAL_INSTRUCTION`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/REPORT_ENCODING_IN_MTVAL_ON_ILLEGAL_INSTRUCTION.yaml`
- **Sail match/evidence:** base.xtval_nonzero → /properties/base/properties/xtval_nonzero [model/core/platform_config.sail:201]
- **Spec evidence/anchor:** src/priv/machine.adoc:2040 [norm:mtval_instr_bits_list]
## `REPORT_ENCODING_IN_STVAL_ON_ILLEGAL_INSTRUCTION`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/REPORT_ENCODING_IN_STVAL_ON_ILLEGAL_INSTRUCTION.yaml`
- **Sail match/evidence:** base.xtval_nonzero → /properties/base/properties/xtval_nonzero [model/core/platform_config.sail:201]
- **Spec evidence/anchor:** src/priv/supervisor.adoc:748 [norm:stval_op_illegal_instr]
## `REPORT_ENCODING_IN_VSTVAL_ON_ILLEGAL_INSTRUCTION`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/REPORT_ENCODING_IN_VSTVAL_ON_ILLEGAL_INSTRUCTION.yaml`
- **Sail match/evidence:** base.xtval_nonzero → /properties/base/properties/xtval_nonzero [model/core/platform_config.sail:201]
- **Spec evidence/anchor:** src/priv/hypervisor.adoc:1375 [norm:vstval_warl]
## `REPORT_ENCODING_IN_VSTVAL_ON_VIRTUAL_INSTRUCTION`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/REPORT_ENCODING_IN_VSTVAL_ON_VIRTUAL_INSTRUCTION.yaml`
- **Sail match/evidence:** base.xtval_nonzero → /properties/base/properties/xtval_nonzero [model/core/platform_config.sail:201]
- **Spec evidence/anchor:** src/priv/hypervisor.adoc:2412 [norm:H_virtinst_xtval]
## `REPORT_GPA_IN_HTVAL_ON_GUEST_PAGE_FAULT`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/REPORT_GPA_IN_HTVAL_ON_GUEST_PAGE_FAULT.yaml`
- **Sail match/evidence:** extensions.H.guest_page_fault_writes_htval → /properties/extensions/properties/H/properties/guest_page_fault_writes_htval [model/core/sys_regs.sail:117]
- **Spec evidence/anchor:** src/priv/hypervisor.adoc:956 [norm:htval_val]
## `REPORT_GPA_IN_TVAL_ON_INSTRUCTION_GUEST_PAGE_FAULT`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/REPORT_GPA_IN_TVAL_ON_INSTRUCTION_GUEST_PAGE_FAULT.yaml`
- **Sail match/evidence:** extensions.H.guest_page_fault_writes_htval → /properties/extensions/properties/H/properties/guest_page_fault_writes_htval [model/core/sys_regs.sail:117]
- **Spec evidence/anchor:** src/priv/hypervisor.adoc:1847 [norm:mtval2_val]
## `REPORT_GPA_IN_TVAL_ON_INTERMEDIATE_GUEST_PAGE_FAULT`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/REPORT_GPA_IN_TVAL_ON_INTERMEDIATE_GUEST_PAGE_FAULT.yaml`
- **Sail match/evidence:** extensions.H.guest_page_fault_writes_htval → /properties/extensions/properties/H/properties/guest_page_fault_writes_htval [model/core/sys_regs.sail:117]
- **Spec evidence/anchor:** src/priv/hypervisor.adoc:1847 [norm:mtval2_val]
## `REPORT_GPA_IN_TVAL_ON_LOAD_GUEST_PAGE_FAULT`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/REPORT_GPA_IN_TVAL_ON_LOAD_GUEST_PAGE_FAULT.yaml`
- **Sail match/evidence:** extensions.H.guest_page_fault_writes_htval → /properties/extensions/properties/H/properties/guest_page_fault_writes_htval [model/core/sys_regs.sail:117]
- **Spec evidence/anchor:** src/priv/hypervisor.adoc:1847 [norm:mtval2_val]
## `REPORT_GPA_IN_TVAL_ON_STORE_AMO_GUEST_PAGE_FAULT`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/REPORT_GPA_IN_TVAL_ON_STORE_AMO_GUEST_PAGE_FAULT.yaml`
- **Sail match/evidence:** extensions.H.guest_page_fault_writes_htval → /properties/extensions/properties/H/properties/guest_page_fault_writes_htval [model/core/sys_regs.sail:117]
- **Spec evidence/anchor:** src/priv/hypervisor.adoc:1847 [norm:mtval2_val]
## `REPORT_VA_IN_MTVAL_ON_BREAKPOINT`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/REPORT_VA_IN_MTVAL_ON_BREAKPOINT.yaml`
- **Sail match/evidence:** base.xtval_nonzero → /properties/base/properties/xtval_nonzero [model/core/platform_config.sail:201]
- **Spec evidence/anchor:** src/priv/machine.adoc:2020 [norm:mtval_enc_img]
## `REPORT_VA_IN_MTVAL_ON_INSTRUCTION_ACCESS_FAULT`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/REPORT_VA_IN_MTVAL_ON_INSTRUCTION_ACCESS_FAULT.yaml`
- **Sail match/evidence:** base.xtval_nonzero → /properties/base/properties/xtval_nonzero [model/core/platform_config.sail:201]
- **Spec evidence/anchor:** src/priv/machine.adoc:2020 [norm:mtval_enc_img]
## `REPORT_VA_IN_MTVAL_ON_INSTRUCTION_MISALIGNED`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/REPORT_VA_IN_MTVAL_ON_INSTRUCTION_MISALIGNED.yaml`
- **Sail match/evidence:** base.xtval_nonzero → /properties/base/properties/xtval_nonzero [model/core/platform_config.sail:201]
- **Spec evidence/anchor:** src/priv/machine.adoc:2020 [norm:mtval_enc_img]
## `REPORT_VA_IN_MTVAL_ON_INSTRUCTION_PAGE_FAULT`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/REPORT_VA_IN_MTVAL_ON_INSTRUCTION_PAGE_FAULT.yaml`
- **Sail match/evidence:** base.xtval_nonzero → /properties/base/properties/xtval_nonzero [model/core/platform_config.sail:201]
- **Spec evidence/anchor:** src/priv/machine.adoc:2020 [norm:mtval_enc_img]
## `REPORT_VA_IN_MTVAL_ON_LOAD_ACCESS_FAULT`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/REPORT_VA_IN_MTVAL_ON_LOAD_ACCESS_FAULT.yaml`
- **Sail match/evidence:** base.xtval_nonzero → /properties/base/properties/xtval_nonzero [model/core/platform_config.sail:201]
- **Spec evidence/anchor:** src/priv/machine.adoc:2020 [norm:mtval_enc_img]
## `REPORT_VA_IN_MTVAL_ON_LOAD_MISALIGNED`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/REPORT_VA_IN_MTVAL_ON_LOAD_MISALIGNED.yaml`
- **Sail match/evidence:** base.xtval_nonzero → /properties/base/properties/xtval_nonzero [model/core/platform_config.sail:201]
- **Spec evidence/anchor:** src/priv/machine.adoc:2020 [norm:mtval_enc_img]
## `REPORT_VA_IN_MTVAL_ON_LOAD_PAGE_FAULT`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/REPORT_VA_IN_MTVAL_ON_LOAD_PAGE_FAULT.yaml`
- **Sail match/evidence:** base.xtval_nonzero → /properties/base/properties/xtval_nonzero [model/core/platform_config.sail:201]
- **Spec evidence/anchor:** src/priv/machine.adoc:2020 [norm:mtval_enc_img]
## `REPORT_VA_IN_MTVAL_ON_STORE_AMO_ACCESS_FAULT`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/REPORT_VA_IN_MTVAL_ON_STORE_AMO_ACCESS_FAULT.yaml`
- **Sail match/evidence:** base.xtval_nonzero → /properties/base/properties/xtval_nonzero [model/core/platform_config.sail:201]
- **Spec evidence/anchor:** src/priv/machine.adoc:2020 [norm:mtval_enc_img]
## `REPORT_VA_IN_MTVAL_ON_STORE_AMO_MISALIGNED`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/REPORT_VA_IN_MTVAL_ON_STORE_AMO_MISALIGNED.yaml`
- **Sail match/evidence:** base.xtval_nonzero → /properties/base/properties/xtval_nonzero [model/core/platform_config.sail:201]
- **Spec evidence/anchor:** src/priv/machine.adoc:2020 [norm:mtval_enc_img]
## `REPORT_VA_IN_MTVAL_ON_STORE_AMO_PAGE_FAULT`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/REPORT_VA_IN_MTVAL_ON_STORE_AMO_PAGE_FAULT.yaml`
- **Sail match/evidence:** base.xtval_nonzero → /properties/base/properties/xtval_nonzero [model/core/platform_config.sail:201]
- **Spec evidence/anchor:** src/priv/machine.adoc:2020 [norm:mtval_enc_img]
## `REPORT_VA_IN_STVAL_ON_BREAKPOINT`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/REPORT_VA_IN_STVAL_ON_BREAKPOINT.yaml`
- **Sail match/evidence:** base.xtval_nonzero → /properties/base/properties/xtval_nonzero [model/core/platform_config.sail:201]
- **Spec evidence/anchor:** src/priv/supervisor.adoc:719 [norm:stval_op_faulting_addr]
## `REPORT_VA_IN_STVAL_ON_INSTRUCTION_ACCESS_FAULT`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/REPORT_VA_IN_STVAL_ON_INSTRUCTION_ACCESS_FAULT.yaml`
- **Sail match/evidence:** base.xtval_nonzero → /properties/base/properties/xtval_nonzero [model/core/platform_config.sail:201]
- **Spec evidence/anchor:** src/priv/supervisor.adoc:719 [norm:stval_op_faulting_addr]
## `REPORT_VA_IN_STVAL_ON_INSTRUCTION_MISALIGNED`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/REPORT_VA_IN_STVAL_ON_INSTRUCTION_MISALIGNED.yaml`
- **Sail match/evidence:** base.xtval_nonzero → /properties/base/properties/xtval_nonzero [model/core/platform_config.sail:201]
- **Spec evidence/anchor:** src/priv/supervisor.adoc:719 [norm:stval_op_faulting_addr]
## `REPORT_VA_IN_STVAL_ON_INSTRUCTION_PAGE_FAULT`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/REPORT_VA_IN_STVAL_ON_INSTRUCTION_PAGE_FAULT.yaml`
- **Sail match/evidence:** base.xtval_nonzero → /properties/base/properties/xtval_nonzero [model/core/platform_config.sail:201]
- **Spec evidence/anchor:** src/priv/supervisor.adoc:719 [norm:stval_op_faulting_addr]
## `REPORT_VA_IN_STVAL_ON_LOAD_ACCESS_FAULT`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/REPORT_VA_IN_STVAL_ON_LOAD_ACCESS_FAULT.yaml`
- **Sail match/evidence:** base.xtval_nonzero → /properties/base/properties/xtval_nonzero [model/core/platform_config.sail:201]
- **Spec evidence/anchor:** src/priv/supervisor.adoc:719 [norm:stval_op_faulting_addr]
## `REPORT_VA_IN_STVAL_ON_LOAD_MISALIGNED`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/REPORT_VA_IN_STVAL_ON_LOAD_MISALIGNED.yaml`
- **Sail match/evidence:** base.xtval_nonzero → /properties/base/properties/xtval_nonzero [model/core/platform_config.sail:201]
- **Spec evidence/anchor:** src/priv/supervisor.adoc:719 [norm:stval_op_faulting_addr]
## `REPORT_VA_IN_STVAL_ON_LOAD_PAGE_FAULT`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/REPORT_VA_IN_STVAL_ON_LOAD_PAGE_FAULT.yaml`
- **Sail match/evidence:** base.xtval_nonzero → /properties/base/properties/xtval_nonzero [model/core/platform_config.sail:201]
- **Spec evidence/anchor:** src/priv/supervisor.adoc:719 [norm:stval_op_faulting_addr]
## `REPORT_VA_IN_STVAL_ON_STORE_AMO_ACCESS_FAULT`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/REPORT_VA_IN_STVAL_ON_STORE_AMO_ACCESS_FAULT.yaml`
- **Sail match/evidence:** base.xtval_nonzero → /properties/base/properties/xtval_nonzero [model/core/platform_config.sail:201]
- **Spec evidence/anchor:** src/priv/supervisor.adoc:719 [norm:stval_op_faulting_addr]
## `REPORT_VA_IN_STVAL_ON_STORE_AMO_MISALIGNED`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/REPORT_VA_IN_STVAL_ON_STORE_AMO_MISALIGNED.yaml`
- **Sail match/evidence:** base.xtval_nonzero → /properties/base/properties/xtval_nonzero [model/core/platform_config.sail:201]
- **Spec evidence/anchor:** src/priv/supervisor.adoc:719 [norm:stval_op_faulting_addr]
## `REPORT_VA_IN_STVAL_ON_STORE_AMO_PAGE_FAULT`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/REPORT_VA_IN_STVAL_ON_STORE_AMO_PAGE_FAULT.yaml`
- **Sail match/evidence:** base.xtval_nonzero → /properties/base/properties/xtval_nonzero [model/core/platform_config.sail:201]
- **Spec evidence/anchor:** src/priv/supervisor.adoc:719 [norm:stval_op_faulting_addr]
## `REPORT_VA_IN_VSTVAL_ON_BREAKPOINT`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/REPORT_VA_IN_VSTVAL_ON_BREAKPOINT.yaml`
- **Sail match/evidence:** base.xtval_nonzero → /properties/base/properties/xtval_nonzero [model/core/platform_config.sail:201]
- **Spec evidence/anchor:** src/priv/hypervisor.adoc:1375 [norm:vstval_warl]
## `REPORT_VA_IN_VSTVAL_ON_INSTRUCTION_ACCESS_FAULT`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/REPORT_VA_IN_VSTVAL_ON_INSTRUCTION_ACCESS_FAULT.yaml`
- **Sail match/evidence:** base.xtval_nonzero → /properties/base/properties/xtval_nonzero [model/core/platform_config.sail:201]
- **Spec evidence/anchor:** src/priv/hypervisor.adoc:1375 [norm:vstval_warl]
## `REPORT_VA_IN_VSTVAL_ON_INSTRUCTION_MISALIGNED`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/REPORT_VA_IN_VSTVAL_ON_INSTRUCTION_MISALIGNED.yaml`
- **Sail match/evidence:** base.xtval_nonzero → /properties/base/properties/xtval_nonzero [model/core/platform_config.sail:201]
- **Spec evidence/anchor:** src/priv/hypervisor.adoc:1375 [norm:vstval_warl]
## `REPORT_VA_IN_VSTVAL_ON_INSTRUCTION_PAGE_FAULT`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/REPORT_VA_IN_VSTVAL_ON_INSTRUCTION_PAGE_FAULT.yaml`
- **Sail match/evidence:** base.xtval_nonzero → /properties/base/properties/xtval_nonzero [model/core/platform_config.sail:201]
- **Spec evidence/anchor:** src/priv/hypervisor.adoc:1375 [norm:vstval_warl]
## `REPORT_VA_IN_VSTVAL_ON_LOAD_ACCESS_FAULT`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/REPORT_VA_IN_VSTVAL_ON_LOAD_ACCESS_FAULT.yaml`
- **Sail match/evidence:** base.xtval_nonzero → /properties/base/properties/xtval_nonzero [model/core/platform_config.sail:201]
- **Spec evidence/anchor:** src/priv/hypervisor.adoc:1375 [norm:vstval_warl]
## `REPORT_VA_IN_VSTVAL_ON_LOAD_MISALIGNED`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/REPORT_VA_IN_VSTVAL_ON_LOAD_MISALIGNED.yaml`
- **Sail match/evidence:** base.xtval_nonzero → /properties/base/properties/xtval_nonzero [model/core/platform_config.sail:201]
- **Spec evidence/anchor:** src/priv/hypervisor.adoc:1375 [norm:vstval_warl]
## `REPORT_VA_IN_VSTVAL_ON_LOAD_PAGE_FAULT`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/REPORT_VA_IN_VSTVAL_ON_LOAD_PAGE_FAULT.yaml`
- **Sail match/evidence:** base.xtval_nonzero → /properties/base/properties/xtval_nonzero [model/core/platform_config.sail:201]
- **Spec evidence/anchor:** src/priv/hypervisor.adoc:1375 [norm:vstval_warl]
## `REPORT_VA_IN_VSTVAL_ON_STORE_AMO_ACCESS_FAULT`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/REPORT_VA_IN_VSTVAL_ON_STORE_AMO_ACCESS_FAULT.yaml`
- **Sail match/evidence:** base.xtval_nonzero → /properties/base/properties/xtval_nonzero [model/core/platform_config.sail:201]
- **Spec evidence/anchor:** src/priv/hypervisor.adoc:1375 [norm:vstval_warl]
## `REPORT_VA_IN_VSTVAL_ON_STORE_AMO_MISALIGNED`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/REPORT_VA_IN_VSTVAL_ON_STORE_AMO_MISALIGNED.yaml`
- **Sail match/evidence:** base.xtval_nonzero → /properties/base/properties/xtval_nonzero [model/core/platform_config.sail:201]
- **Spec evidence/anchor:** src/priv/hypervisor.adoc:1375 [norm:vstval_warl]
## `REPORT_VA_IN_VSTVAL_ON_STORE_AMO_PAGE_FAULT`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/REPORT_VA_IN_VSTVAL_ON_STORE_AMO_PAGE_FAULT.yaml`
- **Sail match/evidence:** base.xtval_nonzero → /properties/base/properties/xtval_nonzero [model/core/platform_config.sail:201]
- **Spec evidence/anchor:** src/priv/hypervisor.adoc:1375 [norm:vstval_warl]
## `RESERVED_VSET_X0X0_VILL_SET`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/RESERVED_VSET_X0X0_VILL_SET.yaml`
- **Sail match/evidence:** extensions.V.reserved_behavior.illegal_vtype → /properties/extensions/properties/V/properties/reserved_behavior/properties/illegal_vtype [model/core/platform_config.sail:312]
- **Spec evidence/anchor:** src/unpriv/vector-common.adoc:1303 [norm:vsetvl_op_rs1_x0_rd_x0]
## `RESERVED_VSET_X0X0_VLMAX_CHANGE`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/RESERVED_VSET_X0X0_VLMAX_CHANGE.yaml`
- **Sail match/evidence:** fixed.vector.vset_vlmax_behavior [model/extensions/V/vext_vset_insts.sail:122]
- **Spec evidence/anchor:** src/unpriv/vector-common.adoc:1303 [norm:vtype_vset_rsv]
## `RVV_VL_WHEN_AVL_LT_DOUBLE_VLMAX`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/RVV_VL_WHEN_AVL_LT_DOUBLE_VLMAX.yaml`
- **Sail match/evidence:** fixed.vector.vl_calculation [model/extensions/V/vext_vset_insts.sail:82]
- **Spec evidence/anchor:** src/unpriv/vector-common.adoc:1333 [norm:vl_val_list]
## `S_MODE_ENDIANNESS`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/S_MODE_ENDIANNESS.yaml`
- **Sail match/evidence:** `mstatus.SBE` field; model does not support changing it [model/core/sys_regs.sail:216] [model/core/sys_regs.sail:255]
- **Spec evidence/anchor:** src/priv/machine.adoc:649 [norm:mstatus_sbe_op]
## `SATP_MODE_BARE`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/SATP_MODE_BARE.yaml`
- **Sail match/evidence:** `extensions.Svbare.supported` → `/properties/extensions/properties/Svbare/properties/supported` [model/core/extensions.sail:578] [model/core/sys_regs.sail:1218]
- **Spec evidence/anchor:** src/priv/supervisor.adoc:1013 [norm:satp_mode]
## `SCONTEXT_IMPLEMENTED`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/SCONTEXT_IMPLEMENTED.yaml`
- **Sail match/evidence:** extensions.Sdtrig.scontext.supported → /properties/extensions/properties/Sdtrig/properties/scontext/properties/supported [model/core/platform_config.sail:15]
- **Spec evidence/anchor:** src/priv/csrs.adoc:250 [CSR list]
## `SCOUNTENABLE_EN`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/SCOUNTENABLE_EN.yaml`
- **Sail match/evidence:** base.scounteren_writable_bits → /properties/base/properties/scounteren_writable_bits [model/core/sys_regs.sail:802]
- **Spec evidence/anchor:** src/priv/supervisor.adoc:511 [norm:scounteren_op]
## `SDTRIG_MCONTROL6_LOAD_WRITABLE`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/SDTRIG_MCONTROL6_LOAD_WRITABLE.yaml`
- **Sail match/evidence:** extensions.Sdtrig.mcontrol6 → /properties/extensions/properties/Sdtrig/properties/mcontrol6 [model/extensions/Sdtrig/sdtrig_types.sail:24]
- **Spec evidence/anchor:** src/unpriv/cmo.adoc:468 [mcontrol6.LOAD mention]
## `SDTRIG_MCONTROL6_SELECT_WRITABLE`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/SDTRIG_MCONTROL6_SELECT_WRITABLE.yaml`
- **Sail match/evidence:** extensions.Sdtrig.mcontrol6 → /properties/extensions/properties/Sdtrig/properties/mcontrol6 [model/extensions/Sdtrig/sdtrig_types.sail:24]
- **Spec evidence/anchor:** src/unpriv/cmo.adoc:422 [mcontrol6.SELECT mention]
## `SDTRIG_MCONTROL6_SIZE_LEGAL_VALUES`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/SDTRIG_MCONTROL6_SIZE_LEGAL_VALUES.yaml`
- **Sail match/evidence:** extensions.Sdtrig.mcontrol6.supported_data_access_sizes → /properties/extensions/properties/Sdtrig/properties/mcontrol6/properties/supported_data_access_sizes [model/extensions/Sdtrig/sdtrig_types.sail:159]
- **Spec evidence/anchor:** src/unpriv/cmo.adoc:432 [mcontrol6.SIZE mention]
## `SDTRIG_MCONTROL6_STORE_WRITABLE`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/SDTRIG_MCONTROL6_STORE_WRITABLE.yaml`
- **Sail match/evidence:** extensions.Sdtrig.mcontrol6 → /properties/extensions/properties/Sdtrig/properties/mcontrol6 [model/extensions/Sdtrig/sdtrig_types.sail:24]
- **Spec evidence/anchor:** src/unpriv/cmo.adoc:445 [mcontrol6.STORE mention]
## `SDTRIG_MCONTROL6_SUPPORTED_TRIGGERS`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/SDTRIG_MCONTROL6_SUPPORTED_TRIGGERS.yaml`
- **Sail match/evidence:** extensions.Sdtrig.mcontrol6.supported → /properties/extensions/properties/Sdtrig/properties/mcontrol6/properties/supported [model/extensions/Sdtrig/sdtrig_control.sail:256]
- **Spec evidence/anchor:** src/unpriv/cmo.adoc:439 [type-6 trigger support mention]
## `SEI_INTR_IMPL`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/SEI_INTR_IMPL.yaml`
- **Sail match/evidence:** extensions.S.interrupts.external.supported → /properties/extensions/properties/S/properties/interrupts/properties/external/properties/supported [model/core/platform_config.sail:198]
- **Spec evidence/anchor:** src/priv/supervisor.adoc:411 [norm:sip_sie_bits_sz]
## `SEW_MIN`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/SEW_MIN.yaml`
- **Sail match/evidence:** fixed.vector.minimum_sew [model/extensions/V/vext_regs.sail:282]
- **Spec evidence/anchor:** src/unpriv/vector-common.adoc:19 [norm:elen]
## `SSEED_READ_ONLY_ZERO`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/SSEED_READ_ONLY_ZERO.yaml`
- **Sail match/evidence:** extensions.Zkr.sseed_read_only_zero → /properties/extensions/properties/Zkr/properties/sseed_read_only_zero [model/core/sys_regs.sail:392]
- **Spec evidence/anchor:** src/priv/machine.adoc:2352 [norm:mseccfg_sseed_useed_op_tbl]
## `SSI_INTR_IMPL`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/SSI_INTR_IMPL.yaml`
- **Sail match/evidence:** extensions.S.interrupts.software.supported → /properties/extensions/properties/S/properties/interrupts/properties/software/properties/supported [model/core/platform_config.sail:196]
- **Spec evidence/anchor:** src/priv/supervisor.adoc:442 [norm:sip_ssip_sie_ssie]
## `SSTATEEN0_FCSR_TYPE`
- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/SSTATEEN0_FCSR_TYPE.yaml`
- **Sail identity:** `extensions.Stateen.sstateen0.FCSR`; hierarchy level `extensions.Stateen.sstateen0`
- **Schema:** `/properties/extensions/properties/Stateen/properties/sstateen0/properties/FCSR`; type `string`; definition `{"description":"core/platform_config.sail:143.39-143.79","enum":["CSRBit_ReadOnlyOne","CSRBit_ReadOnlyZero","CSRBit_Writable"],"type":"string"}`
- **Sail source evidence:** `model/core/platform_config.sail:143-143`
- **Spec mention / defining-location candidate:** `src/priv/smstateen.adoc:251` (extension and setting terms); no normative anchor confidently identified.
- **Defining status:** Spec mention found; first defining location remains unresolved.
- **UDB match:** Semantic match to Sail `extensions.Stateen.sstateen0.FCSR`; UDB `name`, `long_name`, and definition agree with the setting's behavior.
## `STI_INTR_IMPL`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/STI_INTR_IMPL.yaml`
- **Sail match/evidence:** extensions.S.interrupts.timer.supported → /properties/extensions/properties/S/properties/interrupts/properties/timer/properties/supported [model/core/platform_config.sail:15]
- **Spec evidence/anchor:** src/priv/supervisor.adoc:432 [norm:sip_stip_sie_stie]
## `STVAL_WIDTH`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/STVAL_WIDTH.yaml`
- **Sail match/evidence:** xlenbits trap information is written to `stval` [model/sys/sys_control.sail:343]
- **Spec evidence/anchor:** src/priv/supervisor.adoc:708 [norm:stval]
## `STVEC_BASE_ALIGNMENT_VECTORED`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/STVEC_BASE_ALIGNMENT_VECTORED.yaml`
- **Sail match/evidence:** base.stvec.vectored → /properties/base/properties/stvec/properties/vectored [model/core/platform_config.sail:20]
- **Spec evidence/anchor:** src/priv/supervisor.adoc:335 [norm:stvec_sz_base]
## `STVEC_MODES`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/STVEC_MODES.yaml`
- **Sail match/evidence:** base.stvec.vectored → /properties/base/properties/stvec/properties/vectored [model/core/platform_config.sail:20]
- **Spec evidence/anchor:** src/priv/supervisor.adoc:329 [norm:stvec_op]
## `SUPPORT_FRACTIONAL_LMUL_BEYOND_REQUIRED`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/SUPPORT_FRACTIONAL_LMUL_BEYOND_REQUIRED.yaml`
- **Sail match/evidence:** fixed.vector.fractional_lmul [model/extensions/V/vext_regs.sail:265]
- **Spec evidence/anchor:** src/unpriv/vector-common.adoc:295 [norm:vtype_lmul_fval]
## `SUPPORTED_PMLEN_SMMPM`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/SUPPORTED_PMLEN_SMMPM.yaml`
- **Sail match/evidence:** `extensions.Smmpm.supported_pmlen_7` and `_16` → `/properties/extensions/properties/Smmpm/properties/supported_pmlen_7`, `/properties/extensions/properties/Smmpm/properties/supported_pmlen_16` [model/extensions/pointer_masking/pm_types.sail:35] [model/extensions/pointer_masking/pm_types.sail:36]
- **Spec evidence/anchor:** src/priv/zpm.adoc:108 [norm:pmlen_supported_values]
## `SUPPORTED_PMLEN_SMNPM`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/SUPPORTED_PMLEN_SMNPM.yaml`
- **Sail match/evidence:** `extensions.Smnpm.supported_pmlen_7` and `_16` → `/properties/extensions/properties/Smnpm/properties/supported_pmlen_7`, `/properties/extensions/properties/Smnpm/properties/supported_pmlen_16` [model/extensions/pointer_masking/pm_types.sail:38] [model/extensions/pointer_masking/pm_types.sail:39]
- **Spec evidence/anchor:** src/priv/zpm.adoc:108 [norm:pmlen_supported_values]
## `SUPPORTED_PMLEN_SSNPM`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/SUPPORTED_PMLEN_SSNPM.yaml`
- **Sail match/evidence:** `extensions.Ssnpm.supported_pmlen_7` and `_16` → `/properties/extensions/properties/Ssnpm/properties/supported_pmlen_7`, `/properties/extensions/properties/Ssnpm/properties/supported_pmlen_16` [model/extensions/pointer_masking/pm_types.sail:32] [model/extensions/pointer_masking/pm_types.sail:33]
- **Spec evidence/anchor:** src/priv/zpm.adoc:108 [norm:pmlen_supported_values]
## `SV32_VSMODE_TRANSLATION`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/SV32_VSMODE_TRANSLATION.yaml`
- **Sail match/evidence:** extensions.H.vsatp_modes.Sv32 → /properties/extensions/properties/H/properties/vsatp_modes/properties/Sv32 [model/core/sys_regs.sail:99]
- **Spec evidence/anchor:** src/priv/supervisor.adoc:1013 [norm:satp_mode]
## `SV32X4_TRANSLATION`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/SV32X4_TRANSLATION.yaml`
- **Sail match/evidence:** extensions.H.hgatp_modes.Sv32x4 → /properties/extensions/properties/H/properties/hgatp_modes/properties/Sv32x4 [model/core/sys_regs.sail:91]
- **Spec evidence/anchor:** src/priv/hypervisor.adoc:1020 [norm:hgatp_mode_sv]
## `SV39_VSMODE_TRANSLATION`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/SV39_VSMODE_TRANSLATION.yaml`
- **Sail match/evidence:** extensions.H.vsatp_modes.Sv39 → /properties/extensions/properties/H/properties/vsatp_modes/properties/Sv39 [model/core/sys_regs.sail:100]
- **Spec evidence/anchor:** src/priv/supervisor.adoc:1013 [norm:satp_mode]
## `SV39X4_TRANSLATION`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/SV39X4_TRANSLATION.yaml`
- **Sail match/evidence:** extensions.H.hgatp_modes.Sv39x4 → /properties/extensions/properties/H/properties/hgatp_modes/properties/Sv39x4 [model/core/sys_regs.sail:92]
- **Spec evidence/anchor:** src/priv/hypervisor.adoc:1020 [norm:hgatp_mode_sv]
## `SV48_VSMODE_TRANSLATION`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/SV48_VSMODE_TRANSLATION.yaml`
- **Sail match/evidence:** extensions.H.vsatp_modes.Sv48 → /properties/extensions/properties/H/properties/vsatp_modes/properties/Sv48 [model/core/sys_regs.sail:101]
- **Spec evidence/anchor:** src/priv/supervisor.adoc:1013 [norm:satp_mode]
## `SV48X4_TRANSLATION`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/SV48X4_TRANSLATION.yaml`
- **Sail match/evidence:** extensions.H.hgatp_modes.Sv48x4 → /properties/extensions/properties/H/properties/hgatp_modes/properties/Sv48x4 [model/core/sys_regs.sail:93]
- **Spec evidence/anchor:** src/priv/hypervisor.adoc:1020 [norm:hgatp_mode_sv]
## `SV57_VSMODE_TRANSLATION`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/SV57_VSMODE_TRANSLATION.yaml`
- **Sail match/evidence:** extensions.H.vsatp_modes.Sv57 → /properties/extensions/properties/H/properties/vsatp_modes/properties/Sv57 [model/core/sys_regs.sail:102]
- **Spec evidence/anchor:** src/priv/supervisor.adoc:1013 [norm:satp_mode]
## `SV57X4_TRANSLATION`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/SV57X4_TRANSLATION.yaml`
- **Sail match/evidence:** extensions.H.hgatp_modes.Sv57x4 → /properties/extensions/properties/H/properties/hgatp_modes/properties/Sv57x4 [model/core/sys_regs.sail:94]
- **Spec evidence/anchor:** src/priv/hypervisor.adoc:1020 [norm:hgatp_mode_sv]
## `SXLEN`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/SXLEN.yaml`
- **Sail match/evidence:** base.xlen (mode-width limitation) [model/core/xlen.sail:13]
- **Spec evidence/anchor:** src/priv/supervisor.adoc:159 [norm:hint_sxlen]
## `TCONTROL_IMPLEMENTED`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/TCONTROL_IMPLEMENTED.yaml`
- **Sail match/evidence:** extensions.Sdtrig.tcontrol.supported → /properties/extensions/properties/Sdtrig/properties/tcontrol/properties/supported [model/extensions/Sdtrig/sdtrig_control.sail:256]
- **Spec evidence/anchor:** src/priv/csrs.adoc:512 [CSR list]
## `TDATA2_IMPLEMENTED`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/TDATA2_IMPLEMENTED.yaml`
- **Sail match/evidence:** fixed.Sdtrig.tdata2 [model/extensions/Sdtrig/sdtrig_types.sail:175]
- **Spec evidence/anchor:** src/priv/csrs.adoc:509 [CSR list]
## `TDATA3_IMPLEMENTED`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/TDATA3_IMPLEMENTED.yaml`
- **Sail match/evidence:** fixed.Sdtrig.tdata3 [model/extensions/Sdtrig/sdtrig_types.sail:609]
- **Spec evidence/anchor:** src/priv/csrs.adoc:510 [CSR list]
## `TIME_CSR_IMPLEMENTED`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/TIME_CSR_IMPLEMENTED.yaml`
- **Sail match/evidence:** `extensions.Zicntr.supported` → `/properties/extensions/properties/Zicntr/properties/supported`; Sail exposes and reads `time` [model/extensions/Zicntr/zicntr_control.sail:19] [model/extensions/Zicntr/zicntr_control.sail:26] [partial: no separate real-versus-emulated CSR switch]
- **Spec evidence/anchor:** src/priv/machine.adoc:1605 [norm:time_csr_architectural_availability]
## `TINST_VALUE_ON_FINAL_LOAD_GUEST_PAGE_FAULT`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/TINST_VALUE_ON_FINAL_LOAD_GUEST_PAGE_FAULT.yaml`
- **Sail match/evidence:** extensions.H.transformed_instruction.load_guest_page_fault → /properties/extensions/properties/H/properties/transformed_instruction/properties/load_guest_page_fault [model/core/sys_regs.sail:108]
- **Spec evidence/anchor:** src/priv/hypervisor.adoc:2835 [norm:H_trap_xtinst_guestpage]
## `TINST_VALUE_ON_FINAL_STORE_AMO_GUEST_PAGE_FAULT`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/TINST_VALUE_ON_FINAL_STORE_AMO_GUEST_PAGE_FAULT.yaml`
- **Sail match/evidence:** extensions.H.transformed_instruction.samo_guest_page_fault → /properties/extensions/properties/H/properties/transformed_instruction/properties/samo_guest_page_fault [model/core/sys_regs.sail:112]
- **Spec evidence/anchor:** src/priv/hypervisor.adoc:2835 [norm:H_trap_xtinst_guestpage]
## `TINST_VALUE_ON_LOAD_ACCESS_FAULT`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/TINST_VALUE_ON_LOAD_ACCESS_FAULT.yaml`
- **Sail match/evidence:** extensions.H.transformed_instruction.load_access_fault → /properties/extensions/properties/H/properties/transformed_instruction/properties/load_access_fault [model/core/sys_regs.sail:106]
- **Spec evidence/anchor:** src/priv/hypervisor.adoc:2664 [norm:H_trap_xtinst_val]
## `TINST_VALUE_ON_LOAD_ADDRESS_MISALIGNED`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/TINST_VALUE_ON_LOAD_ADDRESS_MISALIGNED.yaml`
- **Sail match/evidence:** extensions.H.transformed_instruction.load_address_misaligned → /properties/extensions/properties/H/properties/transformed_instruction/properties/load_address_misaligned [model/core/sys_regs.sail:105]
- **Spec evidence/anchor:** src/priv/hypervisor.adoc:2664 [norm:H_trap_xtinst_val]
## `TINST_VALUE_ON_LOAD_PAGE_FAULT`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/TINST_VALUE_ON_LOAD_PAGE_FAULT.yaml`
- **Sail match/evidence:** extensions.H.transformed_instruction.load_page_fault → /properties/extensions/properties/H/properties/transformed_instruction/properties/load_page_fault [model/core/sys_regs.sail:107]
- **Spec evidence/anchor:** src/priv/hypervisor.adoc:2664 [norm:H_trap_xtinst_val]
## `TINST_VALUE_ON_STORE_AMO_ACCESS_FAULT`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/TINST_VALUE_ON_STORE_AMO_ACCESS_FAULT.yaml`
- **Sail match/evidence:** extensions.H.transformed_instruction.samo_access_fault → /properties/extensions/properties/H/properties/transformed_instruction/properties/samo_access_fault [model/core/sys_regs.sail:110]
- **Spec evidence/anchor:** src/priv/hypervisor.adoc:2664 [norm:H_trap_xtinst_val]
## `TINST_VALUE_ON_STORE_AMO_ADDRESS_MISALIGNED`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/TINST_VALUE_ON_STORE_AMO_ADDRESS_MISALIGNED.yaml`
- **Sail match/evidence:** extensions.H.transformed_instruction.samo_address_misaligned → /properties/extensions/properties/H/properties/transformed_instruction/properties/samo_address_misaligned [model/core/sys_regs.sail:109]
- **Spec evidence/anchor:** src/priv/hypervisor.adoc:2664 [norm:H_trap_xtinst_val]
## `TINST_VALUE_ON_STORE_AMO_PAGE_FAULT`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/TINST_VALUE_ON_STORE_AMO_PAGE_FAULT.yaml`
- **Sail match/evidence:** extensions.H.transformed_instruction.samo_page_fault → /properties/extensions/properties/H/properties/transformed_instruction/properties/samo_page_fault [model/core/sys_regs.sail:111]
- **Spec evidence/anchor:** src/priv/hypervisor.adoc:2664 [norm:H_trap_xtinst_val]
## `TRAP_ON_EBREAK`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/TRAP_ON_EBREAK.yaml`
- **Sail match/evidence:** EBREAK raises a breakpoint exception [model/extensions/I/base_insts.sail:740]
- **Spec evidence/anchor:** src/priv/machine.adoc:2620 [norm:ebreak_op2]
## `TRAP_ON_ECALL_FROM_M`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/TRAP_ON_ECALL_FROM_M.yaml`
- **Sail match/evidence:** ECALL selects an exception cause from the current privilege mode [model/extensions/I/base_insts.sail:544]
- **Spec evidence/anchor:** src/priv/machine.adoc:2605 [norm:ecall_op2]
## `TRAP_ON_ECALL_FROM_S`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/TRAP_ON_ECALL_FROM_S.yaml`
- **Sail match/evidence:** ECALL selects an exception cause from the current privilege mode [model/extensions/I/base_insts.sail:544]
- **Spec evidence/anchor:** src/priv/machine.adoc:2605 [norm:ecall_op2]
## `TRAP_ON_ECALL_FROM_U`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/TRAP_ON_ECALL_FROM_U.yaml`
- **Sail match/evidence:** ECALL selects an exception cause from the current privilege mode [model/extensions/I/base_insts.sail:544]
- **Spec evidence/anchor:** src/priv/machine.adoc:2605 [norm:ecall_op2]
## `TRAP_ON_ECALL_FROM_VS`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/TRAP_ON_ECALL_FROM_VS.yaml`
- **Sail match/evidence:** ECALL maps VirtualSupervisor to VS-ECALL [model/extensions/I/base_insts.sail:544]
- **Spec evidence/anchor:** src/priv/hypervisor.adoc:2326 [norm:H_cause_ecall]
## `TRAP_ON_ILLEGAL_WLRL`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/TRAP_ON_ILLEGAL_WLRL.yaml`
- **Sail match/evidence:** WLRL VGEIN retains its prior value on an out-of-range write [model/core/sys_regs.sail:357] [model/core/sys_regs.sail:359] [partial: one WLRL field; not a general trap policy]
- **Spec evidence/anchor:** src/priv/priv-csrs.adoc:649 [norm:Zicsr_wlrl_exception]
## `TRAP_ON_RESERVED_INSTRUCTION`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/TRAP_ON_RESERVED_INSTRUCTION.yaml`
- **Sail match/evidence:** Unmatched encodings decode as ILLEGAL and execute as Illegal_Instruction [model/sys/insts_begin.sail:72] [model/postlude/insts_end.sail:15]
- **Spec evidence/anchor:** src/unpriv/rv32.adoc:124 [reserved instruction behavior]
## `TRAP_ON_SFENCE_VMA_WHEN_SATP_MODE_IS_READ_ONLY`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/TRAP_ON_SFENCE_VMA_WHEN_SATP_MODE_IS_READ_ONLY.yaml`
- **Sail match/evidence:** `extensions.Svbare.sfence_vma_illegal_if_svbare_only` → `/properties/extensions/properties/Svbare/properties/sfence_vma_illegal_if_svbare_only` [model/extensions/I/base_insts.sail:776]
- **Spec evidence/anchor:** src/priv/supervisor.adoc:1418 [norm:satp_mode_roz_sfence_illegal]
## `TRAP_ON_UNIMPLEMENTED_CSR`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/TRAP_ON_UNIMPLEMENTED_CSR.yaml`
- **Sail match/evidence:** Failed CSR checks yield CSR_Illegal, mapped by Zicsr to Illegal_Instruction [model/sys/sys_control.sail:60] [model/extensions/Zicsr/zicsr_insts.sail:45]
- **Spec evidence/anchor:** src/priv/ssstrict.adoc:10 [unimplemented CSR access behavior]
## `TRAP_ON_UNIMPLEMENTED_INSTRUCTION`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/TRAP_ON_UNIMPLEMENTED_INSTRUCTION.yaml`
- **Sail match/evidence:** Unmatched encodings decode as ILLEGAL and execute as Illegal_Instruction [model/sys/insts_begin.sail:72] [model/postlude/insts_end.sail:15]
- **Spec evidence/anchor:** src/profiles/rva23.adoc:282 [unimplemented instruction behavior]
## `USEED_READ_ONLY_ZERO`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/USEED_READ_ONLY_ZERO.yaml`
- **Sail match/evidence:** extensions.Zkr.useed_read_only_zero → /properties/extensions/properties/Zkr/properties/useed_read_only_zero [model/core/sys_regs.sail:396]
- **Spec evidence/anchor:** src/priv/machine.adoc:2352 [norm:mseccfg_sseed_useed_op_tbl]
## `UXLEN`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/UXLEN.yaml`
- **Sail match/evidence:** base.xlen (mode-width limitation) [model/core/xlen.sail:13]
- **Spec evidence/anchor:** src/priv/supervisor.adoc:148 [norm:sstatus_uxl_behavior]
## `VECTOR_FF_NO_EXCEPTION_TRIM`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/VECTOR_FF_NO_EXCEPTION_TRIM.yaml`
- **Sail match/evidence:** fixed.vector.fault_only_first [model/extensions/V/vext_mem_insts.sail:135]
- **Spec evidence/anchor:** src/unpriv/vector-common.adoc:1806 [norm:vector_ff_no_exception]
## `VECTOR_FF_SEG_EXCEPTION_PARTIAL_LOAD`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/VECTOR_FF_SEG_EXCEPTION_PARTIAL_LOAD.yaml`
- **Sail match/evidence:** fixed.vector.segment_fault_only_first [model/extensions/V/vext_mem_insts.sail:152]
- **Spec evidence/anchor:** src/unpriv/vector-common.adoc:1955 [norm:vector_ff_seg_partial_access]
## `VECTOR_FF_UPDATE_PAST_TRIM`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/VECTOR_FF_UPDATE_PAST_TRIM.yaml`
- **Sail match/evidence:** fixed.vector.fault_only_first_update [model/extensions/V/vext_mem_insts.sail:167]
- **Spec evidence/anchor:** src/unpriv/vector-common.adoc:1775 [norm:vector_ff_past_trap]
## `VECTOR_LOAD_PAST_TRAP`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/VECTOR_LOAD_PAST_TRAP.yaml`
- **Sail match/evidence:** fixed.vector.load_past_trap [model/extensions/V/vext_mem_insts.sail:82]
- **Spec evidence/anchor:** src/unpriv/vector-common.adoc:1773 [norm:vector_ls_overwrite_past_trap]
## `VECTOR_LOAD_SEG_FF_OVERWRITE_ELEMENTS_AFTER_FAULT`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/VECTOR_LOAD_SEG_FF_OVERWRITE_ELEMENTS_AFTER_FAULT.yaml`
- **Sail match/evidence:** fixed.vector.segment_load_past_trap [model/extensions/V/vext_mem_insts.sail:142]
- **Spec evidence/anchor:** src/unpriv/vector-common.adoc:1959 [norm:vector_ls_seg_ff_overload]
## `VECTOR_LS_INDEX_MAX_EEW`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/VECTOR_LS_INDEX_MAX_EEW.yaml`
- **Sail match/evidence:** extensions.V.max_index_eew_exp → /properties/extensions/properties/V/properties/max_index_eew_exp [model/extensions/V/vext_control.sail:29]
- **Spec evidence/anchor:** src/unpriv/vector-common.adoc:1581 [norm:vector_ls_indexed_eew_emul]
## `VECTOR_LS_MISALIGNED_LEGAL`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/VECTOR_LS_MISALIGNED_LEGAL.yaml`
- **Sail match/evidence:** memory.misaligned.exceptions.vector → /properties/memory/properties/misaligned/properties/exceptions/allOf/0/properties/vector [model/core/platform_config.sail:98]
- **Spec evidence/anchor:** src/unpriv/vector-common.adoc:2201 [norm:vector_ls_misaligned_exception]
## `VECTOR_LS_SEG_PARTIAL_ACCESS`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/VECTOR_LS_SEG_PARTIAL_ACCESS.yaml`
- **Sail match/evidence:** fixed.vector.segment_access [model/extensions/V/vext_mem_insts.sail:139]
- **Spec evidence/anchor:** src/unpriv/vector-common.adoc:1891 [norm:vector_ls_seg_partial_access]
## `VECTOR_LS_WHOLEREG_MISALIGNED_LEGAL`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/VECTOR_LS_WHOLEREG_MISALIGNED_LEGAL.yaml`
- **Sail match/evidence:** memory.misaligned.exceptions.vector → /properties/memory/properties/misaligned/properties/exceptions/allOf/0/properties/vector [model/core/platform_config.sail:98]
- **Spec evidence/anchor:** src/unpriv/vector-common.adoc:2130 [norm:vector_ls_wholereg_misaligned_exception]
## `VENDOR_ID_BANK`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/VENDOR_ID_BANK.yaml`
- **Sail match/evidence:** platform.vendorid → /properties/platform/properties/vendorid [model/core/sys_regs.sail:877] [partial: combined platform.vendorid scalar]
- **Spec evidence/anchor:** src/priv/machine.adoc:226 [norm:mvendorid_enc]
## `VENDOR_ID_OFFSET`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/VENDOR_ID_OFFSET.yaml`
- **Sail match/evidence:** platform.vendorid → /properties/platform/properties/vendorid [model/core/sys_regs.sail:877] [partial: combined platform.vendorid scalar]
- **Spec evidence/anchor:** src/priv/machine.adoc:226 [norm:mvendorid_enc]
## `VFREDUSUM_FINAL_NODE_ELEMENT_BEHAVIOR`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/VFREDUSUM_FINAL_NODE_ELEMENT_BEHAVIOR.yaml`
- **Sail match/evidence:** fixed.vector.vfredusum [model/extensions/V/vext_fp_red_insts.sail:103]
- **Spec evidence/anchor:** src/unpriv/vector-common.adoc:4058 [norm:vfredusum_additive_impl]
## `VFREDUSUM_INACTIVE_NODE_ELEMENT_BEHAVIOR`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/VFREDUSUM_INACTIVE_NODE_ELEMENT_BEHAVIOR.yaml`
- **Sail match/evidence:** fixed.vector.vfredusum [model/extensions/V/vext_fp_red_insts.sail:103]
- **Spec evidence/anchor:** src/unpriv/vector-common.adoc:4058 [norm:vfredusum_additive_impl]
## `VFREDUSUM_NAN`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/VFREDUSUM_NAN.yaml`
- **Sail match/evidence:** fixed.vector.vfredusum [model/extensions/V/vext_fp_red_insts.sail:103]
- **Spec evidence/anchor:** src/unpriv/vector-common.adoc:4061 [norm:vfredusum_redtree]
## `VFREDUSUM_NODE_ROUNDING_BEHAVIOR`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/VFREDUSUM_NODE_ROUNDING_BEHAVIOR.yaml`
- **Sail match/evidence:** fixed.vector.vfredusum [model/extensions/V/vext_fp_red_insts.sail:64]
- **Spec evidence/anchor:** src/unpriv/vector-common.adoc:4036 [norm:vfredusum_op]
## `VILL_SET_ON_RESERVED_VTYPE`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/VILL_SET_ON_RESERVED_VTYPE.yaml`
- **Sail match/evidence:** extensions.V.reserved_behavior.illegal_vtype → /properties/extensions/properties/V/properties/reserved_behavior/properties/illegal_vtype [model/core/platform_config.sail:312]
- **Spec evidence/anchor:** src/unpriv/vector-common.adoc:1262 [norm:vtype_vill_val_vill]
## `VLEN`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/VLEN.yaml`
- **Sail match/evidence:** extensions.V.vlen_exp → /properties/extensions/properties/V/properties/vlen_exp [model/extensions/V/vext_arith_insts.sail:158]
- **Spec evidence/anchor:** src/unpriv/vector-common.adoc:21 [norm:vlen]
## `VMID_WIDTH`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/VMID_WIDTH.yaml`
- **Sail match/evidence:** memory.vmidlen → /properties/memory/properties/vmidlen [model/core/xlen.sail:26]
- **Spec evidence/anchor:** src/priv/hypervisor.adoc:1087 [norm:hgatp_vmid]
## `VS_MODE_ENDIANNESS`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/VS_MODE_ENDIANNESS.yaml`
- **Sail match/evidence:** `hstatus.VSBE` field; model does not support changing it [model/core/sys_regs.sail:343] [model/core/sys_regs.sail:365]
- **Spec evidence/anchor:** src/priv/hypervisor.adoc:336 [norm:hstatus_vsbe_op]
## `VSSTAGE_MODE_BARE`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/VSSTAGE_MODE_BARE.yaml`
- **Sail match/evidence:** extensions.H.vsatp_modes → /properties/extensions/properties/H/properties/vsatp_modes [model/core/platform_config.sail:44]
- **Spec evidence/anchor:** src/priv/hypervisor.adoc:1421 [norm:vsatp_v0]
## `VSSTATUS_VS_EXISTS`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/VSSTATUS_VS_EXISTS.yaml`
- **Sail match/evidence:** Sail defines `vsstatus` and makes it accessible when H is enabled [model/core/sys_regs.sail:1021] [model/core/sys_regs.sail:1029]
- **Spec evidence/anchor:** src/unpriv/vector-common.adoc:144 [norm:vsstatus_vs_exists]
## `VSTVEC_MODES`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/VSTVEC_MODES.yaml`
- **Sail match/evidence:** base.vstvec.vectored → /properties/base/properties/vstvec/properties/vectored [model/core/platform_config.sail:20]
- **Spec evidence/anchor:** src/priv/hypervisor.adoc:1303 [norm:vstvec_sz_acc_op]
## `VSXLEN`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/VSXLEN.yaml`
- **Sail match/evidence:** base.xlen (mode-width limitation) [model/core/xlen.sail:13]
- **Spec evidence/anchor:** src/priv/hypervisor.adoc:1181 [norm:vsstatus_uxl_op]
## `VUXLEN`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/VUXLEN.yaml`
- **Sail match/evidence:** base.xlen (mode-width limitation) [model/core/xlen.sail:13]
- **Spec evidence/anchor:** src/priv/hypervisor.adoc:1181 [norm:vsstatus_uxl_op]
## `WFI_FINITE`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/WFI_FINITE.yaml`
- **Sail match/evidence:** `platform.max_time_to_wait` bounds the external harness wait increment [model/core/platform_config.sail:188] [model/core/platform_config.sail:190] → `/properties/platform/properties/max_time_to_wait` [partial: external-harness wait bound]
- **Spec evidence/anchor:** src/priv/machine.adoc:754 [norm:mstatus_tw_op]
## `WFI_U_MODE`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/WFI_U_MODE.yaml`
- **Sail match/evidence:** platform.wfi_available_to_user_mode → /properties/platform/properties/wfi_available_to_user_mode [model/core/platform_config.sail:186]
- **Spec evidence/anchor:** src/priv/machine.adoc:2685 [norm:wfi_opt_U_mode]
## `ZAWRS_NTO_IS_NOP`

- **Class:** `0b111`
- **UDB YAML:** `spec/std/isa/param/ZAWRS_NTO_IS_NOP.yaml`
- **Sail match/evidence:** extensions.Zawrs.nto.is_nop → /properties/extensions/properties/Zawrs/properties/nto/properties/is_nop [model/postlude/step.sail:241]
- **Spec evidence/anchor:** src/unpriv/zawrs.adoc:25 [norm:Zawrs_wrs-nto_stall_exec]
