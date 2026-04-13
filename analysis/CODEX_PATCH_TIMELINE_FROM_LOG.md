# Codex Patch Timeline Extract (codex.txt)

## Summary

- Source: `D:\Projects\PortaRe0\software\log\codex.txt`
- Marker observations: 112
- Distinct marker states: 66
- Interesting event observations: 108

## Key Findings

- `codex.txt` contains repeated live-media rewrites of both `F:\EFI\BOOT\BOOTAA64.EFI` and `F:\EFI\Microsoft\Boot\bootmgfw.efi`.
- `No mapping` and `BCD` results must therefore be interpreted together with the active patch marker, not as pure UEFI behavior.
- The transcript explicitly identifies `0x1003BA6C` as a `No mapping` regression candidate and later switches to a safer variant that NOPs the cleanup helper.

## Distinct Marker States

- line 14: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic...` | `PATCH_VAS=0x101B572C,` | `SHA256=f2d3da1b5fc7cf33938bcee524a83ada27577f67d5f58acc5b88b8a307178cde`
- line 17: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic...` | `PATCH_VAS=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AF38` | `SHA256=f2d3da1b5fc7cf33938bcee524a83ada27577f67d5f58acc5b88b8a307178cde`
- line 141: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic...` | `PATCH_VAS=0x101B572C` | `SHA256=cd756e7981c85d188c2cfdc09477381de20d8856384dcb86d45d8424ac0dd753`
- line 144: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic...` | `PATCH_VAS=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC` | `SHA256=cd756e7981c85d188c2cfdc09477381de20d8856384dcb86d45d8424ac0dd753`
- line 252: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic...` | `SHA256=e2212c5940e9c63fa06f67c3cc36ac78a281190ab1c68272c197`
- line 255: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic...` | `PATCH_VAS=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003AFF4` | `SHA256=e2212c5940e9c63fa06f67c3cc36ac78a281190ab1c68272c19782d704d40dcc`
- line 652: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic...` | `PATCH_VAS=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B040` | `SHA256=93b2258de0a937a0a55649321bebcee77764a69c1a4d677f7ca15b8682dfd170`
- line 1048: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic...` | `PATCH_VAS=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B1F0` | `SHA256=b6549986fcd6efab902a750819ad050a6256b6472fe909ab4e00b754f49bc6c4`
- line 1499: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic...` | `PATCH_VAS=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B49C` | `SHA256=2be3653bb5a2305b709d6b399a0c8876b6f1ef6d4034d25d69ab88230ec007db`
- line 1751: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic...`
- line 1780: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic...` | `PATCH_VAS=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0`
- line 1836: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic...` | `SHA256=3181a1fda96a7b`
- line 1839: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic...` | `PATCH_VAS=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0` | `SHA256=3181a1fda96a7bbe79b5917c810160d005d68885873a5126c9765dfb2a1987a2`
- line 1935: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic...` | `SHA256=3181a1fda96a7bbe79b5917c810160d005d68885873a5126c9765dfb2a1987a2`
- line 1938: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic...` | `PATCH_VAS=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003B4EC` | `SHA256=3181a1fda96a7bbe79b5917c810160d005d68885873a5126c9765dfb2a1987a2`
- line 1989: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic...` | `SHA256=5f8`
- line 1992: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic...` | `PATCH_VAS=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003B4EC` | `SHA256=5f8f6693522d3e3bd6a8ade1ff6aab8893a8db7ff5d5e77e744e6973a03ce42f`
- line 2123: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic...` | `SHA256=ff6ead665c0bcaea0ddf93b7f90ba08db8b2ba21488954912dfbbe8c5bf49209`
- line 2126: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic...` | `PATCH_VAS=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003B528` | `SHA256=ff6ead665c0bcaea0ddf93b7f90ba08db8b2ba21488954912dfbbe8c5bf49209`
- line 2207: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic...` | `SHA256=ff6ead665c0bcaea0ddf93b7f90ba08db8b2ba21488954912dfbbe8c5bf49209`
- line 2210: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic...` | `PATCH_VAS=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003B544` | `SHA256=ff6ead665c0bcaea0ddf93b7f90ba08db8b2ba21488954912dfbbe8c5bf49209`
- line 2247: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic...` | `SHA256=e8a2a7ad86b153021fc3101df6609dab94bbe727275fe7f0086443498d27721b`
- line 2250: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic...` | `PATCH_VAS=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003B544` | `SHA256=e8a2a7ad86b153021fc3101df6609dab94bbe727275fe7f0086443498d27721b`
- line 2334: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic...` | `PATCH_VAS=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003B598` | `SHA256=e8a2a7ad86b153021fc3101df6609dab94bbe727275fe7f0086443498d27721b`
- line 2362: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic...`
- line 2384: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic...` | `SHA256=b916c0dfb326795c5f1e4157d54353b25ca164feacebc9fb58ec0de905d38bb3`
- line 2387: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic...` | `PATCH_VAS=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003B598` | `SHA256=b916c0dfb326795c5f1e4157d54353b25ca164feacebc9fb58ec0de905d38bb3`
- line 2475: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic...` | `SHA256=b916c0dfb326795c5f1e4157d54353b25ca164feacebc9fb58ec0de905d38bb3`
- line 2478: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic...` | `PATCH_VAS=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003B5B8` | `SHA256=b916c0dfb326795c5f1e4157d54353b25ca164feacebc9fb58ec0de905d38bb3`
- line 2488: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic...` | `SHA256=b003fe4f55c65d422411bea2cbd470a86a35d3fe649b9682f04e5548062160aa`
- line 2491: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic...` | `PATCH_VAS=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003B5B8` | `SHA256=b003fe4f55c65d422411bea2cbd470a86a35d3fe649b9682f04e5548062160aa`
- line 2628: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic...` | `SHA256=74c6d93be9292c26d7b62adf9789bf5d45eb1f3d2de4f7bbe97ccc3066bf5edf`
- line 2631: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic...` | `PATCH_VAS=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003B5DC` | `SHA256=74c6d93be9292c26d7b62adf9789bf5d45eb1f3d2de4f7bbe97ccc3066bf5edf`
- line 2731: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic...` | `SHA256=39895b48eae6d9a1137c955b31e5221ba89c7f9482d87f0bc41c5132ffcdc11d`
- line 2734: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic...` | `PATCH_VAS=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003B6A0` | `SHA256=39895b48eae6d9a1137c955b31e5221ba89c7f9482d87f0bc41c5132ffcdc11d`
- line 2764: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic...` | `SHA256=9bd752fa0ec8b2da2ef1ad4669549363636e56b5714e066c16555c17cc11e722`
- line 2767: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic...` | `PATCH_VAS=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003B6A0` | `SHA256=9bd752fa0ec8b2da2ef1ad4669549363636e56b5714e066c16555c17cc11e722`
- line 2860: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic...` | `SHA256=a4bc27d6390b93adad5dce6d57f2cd17f6eae84c5291cd8b9867a04a3f54bc4e`
- line 2863: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic...` | `PATCH_VAS=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003B6C4` | `SHA256=a4bc27d6390b93adad5dce6d57f2cd17f6eae84c5291cd8b9867a04a3f54bc4e`
- line 2893: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic...` | `SHA256=071bc177eac2736c276e994b6a1305c88fec6b08cb540e2a137834d720f5c527`
- ... 26 more marker states omitted

## Key Event Timeline

- line 42 | `bcd_000d` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AF38, sha=f2d3da1b5fc7`
  0x101AEDB8 は success で返っています。なので BCD 0xc000000d の本体は、その次の success path 側です。
- line 328 | `bcd_000d` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003AFF4, sha=e2212c5940e9`
  • 新しい run を確認して、今回の patch が発火したかと BCD 0xc000000d の直前経路を見ます。
- line 3530 | `bcd_0098` | `2026-04-04 20:50:13.321` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BB08, sha=2a0a7c32488d`
  [2026-04-04 20:50:13.321] 13;001HFile: \BCDStatus: 0xc0000098Info:
- line 3570 | `bcd_0098` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BB08, sha=2a0a7c32488d`
  • この run は 0x1003BB08 に届かず、そのまま Windows Boot Manager / \BCD / 0xc0000098 画面に入っています。つまり前回の path は途中で変
- line 3616 | `bcd_0098` | `2026-04-05 00:22:18.004` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BAEC, sha=f1462e346740`
  [2026-04-05 00:22:18.004] File: \BCDStatus: 0xc0000098Info:
- line 3621 | `bcd_0098` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BAEC, sha=f1462e346740`
  • latest run は 0x1003BAEC を踏まずにそのまま 0xc0000098 画面へ行きました。いちばん筋がいい仮説は 0x1003B9F0 の loop-back なので、次は
- line 3641 | `bcd_0098` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BAEC, sha=f1462e346740`
  File: \BCD / Status: 0xc0000098 の画面に入っています。つまりこの run は 0x1003BAEC より前で別の枝を取っていて、そこが今の分岐点で
- line 3654 | `bcd_0098` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BAEC, sha=f1462e346740`
  • 最新の run と live の patch marker を見ます。まず 0x1003B9F0 に来たか、あるいは別枝で 0xc0000098 に落ちたかを確認します。
- line 3813 | `bcd_0098` | `2026-04-05 02:00:50.204` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BAEC, sha=f1462e346740`
  [2026-04-05 02:00:50.204] 1HFile: \BCDStatus: 0xc0000098Info:
- line 3934 | `bcd_0098` | `2026-04-05 02:08:15.909` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA5C, sha=12e69c309102`
  [2026-04-05 02:08:15.909] 1HFile: \BCDStatus: 0xc0000098Info:
- line 3980 | `bcd_0098` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA5C, sha=12e69c309102`
  \BCD / 0xc0000098 の画面に入っています。つまり 0x1003BA5C に到達する前に、直前の helper call が非復帰で screen path に入っている可能
- line 4013 | `bcd_0098` | `2026-04-05 02:12:59.571` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA58, sha=9bfdf4c1e3c0`
  [2026-04-05 02:12:59.571] 01HFile: \BCDStatus: 0xc0000098Info:
- line 4038 | `bcd_0098` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA58, sha=9bfdf4c1e3c0`
  \BCD / 0xc0000098 画面へ入っています。つまり bl 0x100451D8 の call site 自体には到達していません。
- line 4248 | `bcd_0098` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA54, sha=2a745364c37b`
  • Ran $m = Select-String -Path 'D:\Projects\PortaRe0\software\log\teraterm.log' -Pattern 'Windows Boot Manager|Status: 0xc0000098|
- line 4294 | `bcd_0098` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA54, sha=2a745364c37b`
  Status: 0xc0000098 でした。前の run では 2026-04-05 02:44:13 に ELR=0x23CCE7A54 が出ていて、0x1003BA54 の call site 直前までは来てい
- line 4661 | `no_mapping` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA54,0x1003BA58,0x1003BA6C, sha=42c041edca4a`
  • 今回の run は shell からの chainload が別問題を起こしています。BOOTAA64.EFI 自体は見つかっていますが、StartImage が No mapping で落
- line 4672 | `no_mapping` | `2026-04-05 18:48:02.017` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA54,0x1003BA58,0x1003BA6C, sha=42c041edca4a`
  • Ran rg -n "No mapping|TESTA7Z|startup.nsh|bootmgfw\.efi|LoadImage|StartImage" 'D:\Projects\porta-a733-bringup' 'D:
- line 4686 | `no_mapping` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA54,0x1003BA58,0x1003BA6C, sha=42c041edca4a`
  • shell から BOOTAA64.EFI を直接叩くと StartImage failed: No mapping です。以前の導線メモ通り、ここは BootProbe/TESTA7Z 側を使うのが筋
- line 4714 | `no_mapping` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA54,0x1003BA58,0x1003BA6C, sha=42c041edca4a`
  • Ran rg -n "StartImage failed: No mapping|No mapping|startup.nsh|BOOTAA64.EFI" 'D:\Projects\PortaRe0\software\agents\PROGRESS.md' 'D:
- line 4773 | `no_mapping` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA54,0x1003BA58,0x1003BA6C, sha=42c041edca4a`
  • Ran rg -n "No mapping|EfiBootManagerBoot|LoadImage \(TRUE|LoadImage \(FALSE|BootPolicy|PlatformBootManagerAfterConsole entered" 'D:
- line 4823 | `no_mapping` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA54,0x1003BA58,0x1003BA6C, sha=42c041edca4a`
  • No mapping は診断用の LoadImage(TRUE) 経路が原因の可能性が高いです。なので、標準の EfiBootManagerBoot() 経路へ戻す差分を探して、その
- line 4881 | `no_mapping` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA54,0x1003BA58,0x1003BA6C, sha=42c041edca4a`
  • EfiBootManagerBoot() の API 定義は取れました。次は BootDevicePathOnce() を標準 boot option 化して、No mapping が消えるかを試します。
- line 5115 | `no_mapping` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA54,0x1003BA58,0x1003BA6C, sha=42c041edca4a`
  • この run は deep patch の続きではなく、loader 起動経路そのものがまた崩れています。No mapping と shell 側の探索失敗が同時に出ているの
- line 5128 | `no_mapping` | `2026-04-05 18:58:04.209` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA54,0x1003BA58,0x1003BA6C, sha=42c041edca4a`
  [2026-04-05 18:58:06.303] [A733-BOOT] Heartbeat 125 Event=23DC07118 Handle=23D2C0698 Base=23CCAB000 Started=1 Status=No mapping
- line 5145 | `no_mapping` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA54,0x1003BA58,0x1003BA6C, sha=42c041edca4a`
  • この run では deep path が途中で No mapping を返していて、前に追っていた 0x1003BA6C まで戻っていません。BCD と shell 側の launch 条
- line 5173 | `regression` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA54,0x1003BA58,0x1003BA6C, sha=42c041edca4a`
  • live の BCD 自体は生きていて、configaccesspolicy と custom:2600002a も入っています。なので、いまの regression は BCD 破損より launch
- line 5174 | `no_mapping` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA54,0x1003BA58,0x1003BA6C, sha=42c041edca4a`
  path 側の可能性が高いです。screen text が途中で出ているかどうかを見て、No mapping が表示経由の戻りなのか即エラーなのかを切ります。
- line 5181 | `bcd_0098` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA54,0x1003BA58,0x1003BA6C, sha=42c041edca4a`
  │ \BCD|File: \\EFI\\Microsoft\\Boot\\BCD|0xc0000098|0xc000000d' | Select-Object -Last 60 | ForEach-Object { $_.Line }
- line 5181 | `bcd_000d` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA54,0x1003BA58,0x1003BA6C, sha=42c041edca4a`
  │ \BCD|File: \\EFI\\Microsoft\\Boot\\BCD|0xc0000098|0xc000000d' | Select-Object -Last 60 | ForEach-Object { $_.Line }
- line 5321 | `no_mapping` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic...`
  の EfiBootManagerBoot() が F:/EFI/BOOT/BOOTAA64.EFI を起動し、18:58:06 に No mapping で返っています。その後 shell の F:/startup.nsh
- line 5322 | `no_mapping` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic...`
  も FS1:\EFI\Microsoft\Boot\bootmgfw.efi を見つけていますが、これも即 No mapping、さらに \EFI\BOOT\BOOTAA64.EFI を再実行しても最後は
- line 5323 | `no_mapping` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic...`
  No mapping でした。今回は ELR= も Windows Boot Manager 画面も出ていません。
- line 5336 | `no_mapping` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic...`
  • 新しい run で 0x1003B1F0 に戻れたか、それともまだ No mapping 側かを先に切ります。
- line 5362 | `no_mapping` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA54,0x1003BA58,0x1003B1F0, sha=5c8ccb4038bd`
  • いまの run で分岐は re-locate できました。0x1003B1F0 には戻れていて、No mapping 側ではなく、以前の success-path に復帰しています。次
- line 5439 | `no_mapping` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic...`
  • 今回の D:/Projects/PortaRe0/software/log/teraterm.log では、No mapping 側には落ちていません。2026-04-05 19:26:36 に狙い通り
- line 5867 | `live_sync` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic...`
  • 反映は終わりました。live の F:/EFI/BOOT/BOOTAA64.EFI と F:/EFI/Microsoft/Boot/bootmgfw.efi は同じ 0x1003B448 版で、SHA256 は両方
- line 5878 | `no_mapping` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic...`
  理由は、いまはもう前半の No mapping や runtime 復帰そのものではなく、bootmgfw のかなり深い後段を追えているからです。最新では
- line 5977 | `live_sync` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic...`
  次の版はもう反映済みです。live の F:/EFI/BOOT/BOOTAA64.EFI と F:/EFI/Microsoft/Boot/bootmgfw.efi は両方 0x1003B460 版で、SHA256 は
- line 6074 | `live_sync` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic...`
  • 反映は済みました。live の F:/EFI/BOOT/BOOTAA64.EFI と F:/EFI/Microsoft/Boot/bootmgfw.efi は今 0x1003B49C 版で、SHA256 は
- line 6223 | `no_mapping` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA54,0x1003BA58,0x1003BA6C, sha=42c041edca4a`
  • 今回の run は deep stop まで戻らず、StartImage ... No mapping に戻っています。まず shell fallback を確実に通すために、live の
- line 6295 | `no_mapping` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA54,0x1003BA58,0x1003BA6C, sha=42c041edca4a`
  • live の startup.nsh は修正済みです。direct boot の No mapping 自体はまだ残っていますが、次の run では shell fallback が fs4+ も拾え
- line 6314 | `no_mapping` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA54,0x1003BA58,0x1003BA6C, sha=42c041edca4a`
  • 今回の D:/Projects/PortaRe0/software/log/teraterm.log は deep stop には戻っていません。00:33:51 に StartImage ... No mapping で落ち
- line 6330 | `no_mapping` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA54,0x1003BA58,0x1003BA6C, sha=42c041edca4a`
  • 新しい run を見ます。fallback が通ったか、deep path に戻ったか、No mapping のままかをまず切ります。
- line 6346 | `no_mapping` | `2026-04-06 01:13:08.681` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA54,0x1003BA58,0x1003BA6C, sha=42c041edca4a`
  • Ran Select-String -Path 'D:\Projects\PortaRe0\software\log\teraterm.log' -Pattern 'No mapping|Windows Boot Manager|ELR=|not found on
- line 6349 | `no_mapping` | `2026-04-06 01:11:52.657` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA54,0x1003BA58,0x1003BA6C, sha=42c041edca4a`
  Base=23CCAB000 Started=1 Status=No mapping
- line 6403 | `no_mapping` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA54,0x1003BA58,0x1003BA6C, sha=42c041edca4a`
  • 今回の D:/Projects/PortaRe0/software/log/teraterm.log では、01:13:08 にまた StartImage ... No mapping で落ちて、その後 shell 側も
- line 6419 | `no_mapping` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA54,0x1003BA58,0x1003BA6C, sha=42c041edca4a`
  • 新しい run を見ます。current-volume fallback が効いたか、No mapping のままか、もしくは deep path に戻ったかを切ります。
- line 6428 | `no_mapping` | `2026-04-06 01:21:34.099` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA54,0x1003BA58,0x1003BA6C, sha=42c041edca4a`
  • Ran Select-String -Path 'D:\Projects\PortaRe0\software\log\teraterm.log' -Pattern 'No mapping|Windows Boot Manager|ELR=|not found on
- line 6431 | `no_mapping` | `2026-04-06 01:20:18.061` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA54,0x1003BA58,0x1003BA6C, sha=42c041edca4a`
  └ [2026-04-06 01:20:18.061] [A733-BOOT] Heartbeat 125 Event=23DC07118 Handle=23D2C0698 Base=23CCAB000 Started=1 Status=No mapping
- line 6432 | `no_mapping` | `2026-04-06 01:20:18.061` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA54,0x1003BA58,0x1003BA6C, sha=42c041edca4a`
  [2026-04-06 01:20:18.062] Error: Image at 0023CCAB000 start failed: No mapping
- line 6446 | `no_mapping` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA54,0x1003BA58,0x1003BA6C, sha=42c041edca4a`
  • 今回の regression は deep combined patch 側です。前に確実に通っていた 0x1003B49C 版へ一度戻して、まず No mapping から脱出します。
- line 6446 | `regression` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA54,0x1003BA58,0x1003BA6C, sha=42c041edca4a`
  • 今回の regression は deep combined patch 側です。前に確実に通っていた 0x1003B49C 版へ一度戻して、まず No mapping から脱出します。
- line 6487 | `no_mapping` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic...`
  • stable な 0x1003B49C 版へ戻しました。live の BOOT/bootmgfw と marker を揃えて、まず No mapping を消しにいきます。
- line 6504 | `no_mapping` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003B49C, sha=2be3653bb5a2`
  • 今回の D:/Projects/PortaRe0/software/log/teraterm.log では、01:21:34 にまた StartImage ... No mapping で落ちて、その後 shell も
- line 6506 | `regression` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003B49C, sha=2be3653bb5a2`
  ず、主因は deep combined patch 側の regression です。
- line 6508 | `live_sync` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003B49C, sha=2be3653bb5a2`
  そこは戻しました。live の F:/EFI/BOOT/BOOTAA64.EFI と F:/EFI/Microsoft/Boot/bootmgfw.efi は、前に確実に通っていた 0x1003B49C 版へ差
- line 6512 | `no_mapping` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003B49C, sha=2be3653bb5a2`
  この SD で 1 回起動して、新しい D:/Projects/PortaRe0/software/log/teraterm.log をください。次はまず No mapping が消えて
- line 6522 | `no_mapping` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003B49C, sha=2be3653bb5a2`
  れたら、最近は StartImage ... No mapping に崩れて、bootmgfw 本体まで入れない run が混ざるようになりました。なので、まずは安定してい
- line 6523 | `no_mapping` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003B49C, sha=2be3653bb5a2`
  た 0x1003B49C 版へ戻して、No mapping を消して本流へ復帰させる段階です。
- line 6532 | `no_mapping` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003B49C, sha=2be3653bb5a2`
  • stable な 0x1003B49C 版へ戻した run を確認します。No mapping が消えたか、ELR=...649C に復帰したかをまず見ます。
- line 6548 | `no_mapping` | `2026-04-06 01:40:36.187` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003B49C, sha=2be3653bb5a2`
  • Ran Select-String -Path 'D:\Projects\PortaRe0\software\log\teraterm.log' -Pattern 'No mapping|Windows Boot Manager|ELR=|StartImage
- line 6642 | `no_mapping` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic...`
  • 戻せました。今回の D:/Projects/PortaRe0/software/log/teraterm.log では No mapping は消えて、2026-04-06 01:41:14 JST に
- line 6642 | `restored` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic...`
  • 戻せました。今回の D:/Projects/PortaRe0/software/log/teraterm.log では No mapping は消えて、2026-04-06 01:41:14 JST に
- line 6645 | `live_sync` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic...`
  そのまま 1 段進めて、live の F:/EFI/BOOT/BOOTAA64.EFI と F:/EFI/Microsoft/Boot/bootmgfw.efi は今 0x1003B4B0 で止める版です。SHA256
- line 6670 | `no_mapping` | `2026-04-06 02:09:54.284` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic...`
  • Ran Select-String -Path 'D:\Projects\PortaRe0\software\log\teraterm.log' -Pattern 'ELR=|No mapping|Windows Boot Manager|Status: 0x|
- line 6724 | `live_sync` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003B4EC, sha=5f8f6693522d`
  その blocker を跨ぐ次の版に進めました。live の F:/EFI/BOOT/BOOTAA64.EFI と F:/EFI/Microsoft/Boot/bootmgfw.efi は今 0x1003B4EC で止め
- line 6755 | `no_mapping` | `2026-04-06 02:16:44.244` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003B4EC, sha=5f8f6693522d`
  • Ran Select-String -Path 'D:\Projects\PortaRe0\software\log\teraterm.log' -Pattern 'ELR=|No mapping|Windows Boot Manager|Status: 0x|
- line 6907 | `live_sync` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003B528, sha=ff6ead665c0b`
  そのまま次の stop point に進めました。live の F:/EFI/BOOT/BOOTAA64.EFI と F:/EFI/Microsoft/Boot/bootmgfw.efi は今 0x1003B528 で止め
- line 6927 | `no_mapping` | `2026-04-06 03:18:08.807` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003B528, sha=ff6ead665c0b`
  • Ran Select-String -Path 'D:\Projects\PortaRe0\software\log\teraterm.log' -Pattern 'ELR=|No mapping|Windows Boot Manager|Status: 0x|
- line 7084 | `live_sync` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003B544, sha=e8a2a7ad86b1`
  その次の版に進めました。live の F:/EFI/BOOT/BOOTAA64.EFI と F:/EFI/Microsoft/Boot/bootmgfw.efi は今 0x1003B544 で止める版です。
- line 7104 | `no_mapping` | `2026-04-06 03:49:05.778` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003B544, sha=e8a2a7ad86b1`
  • Ran Select-String -Path 'D:\Projects\PortaRe0\software\log\teraterm.log' -Pattern 'ELR=|No mapping|Windows Boot Manager|Status: 0x|
- line 7232 | `live_sync` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003B598, sha=b916c0dfb326`
  そのまま次の stop point に進めました。live の F:/EFI/BOOT/BOOTAA64.EFI と F:/EFI/Microsoft/Boot/bootmgfw.efi は今 0x1003B598 で止め
- line 7252 | `no_mapping` | `2026-04-06 03:59:43.298` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003B598, sha=b916c0dfb326`
  • Ran Select-String -Path 'D:\Projects\PortaRe0\software\log\teraterm.log' -Pattern 'ELR=|No mapping|Windows Boot Manager|Status: 0x|
- line 7341 | `live_sync` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003B598, sha=b916c0dfb326`
  で、SD が戻ったら live の F:/EFI/BOOT/BOOTAA64.EFI と F:/EFI/Microsoft/Boot/bootmgfw.efi をその版に差し替えて続けます。今の SD 上の
- line 7442 | `live_sync` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003B5B8, sha=b003fe4f55c6`
  • 反映は確認できました。live の F:/EFI/BOOT/BOOTAA64.EFI と F:/EFI/Microsoft/Boot/bootmgfw.efi は両方 0x1003B5B8 版で、SHA256 は
- line 7469 | `no_mapping` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003B5B8, sha=b003fe4f55c6`
  │ $log -Pattern 'ELR=|Windows Boot Manager|Status:|File:|No mapping|A733-EXC' | Select-Object -Last 40 | ForEach-Object
- line 7549 | `no_mapping` | `2026-04-06 13:23:37.842` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003B5B8, sha=b003fe4f55c6`
  │ Windows Boot Manager|Status:|File:|No mapping|A733-EXC' | Select-Object -Last 40 | ForEach-Object { $_.Line }
- line 8226 | `live_sync` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003B5B8, sha=b003fe4f55c6`
  ただ今は F: が消えていて、live の F:/EFI/BOOT/BOOTAA64.EFI と F:/EFI/Microsoft/Boot/bootmgfw.efi にはまだ反映できていません。SD を挿
- line 8247 | `live_sync` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003B5B8, sha=b003fe4f55c6`
  • 反映は終わりました。live の F:/EFI/BOOT/BOOTAA64.EFI と F:/EFI/Microsoft/Boot/bootmgfw.efi は両方 0x1003BB08 版で、SHA256 は
- line 8266 | `no_mapping` | `2026-04-06 19:27:13.497` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003B5B8, sha=b003fe4f55c6`
  │ Windows Boot Manager|Status:|File:|No mapping|A733-EXC' | Select-Object -Last 60 | ForEach-Object { $_.Line }
- line 8270 | `bcd_0098` | `2026-04-06 19:27:13.497` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003B5B8, sha=b003fe4f55c6`
  assistance. File: \BCDStatus: 0xc0000098Info:
- line 8299 | `live_sync` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003B5B8, sha=b003fe4f55c6`
  いま SD 側はもうその次に進んでいます。live の F:/EFI/BOOT/BOOTAA64.EFI と F:/EFI/Microsoft/Boot/bootmgfw.efi は 0x1003BB08 版で、
- line 8319 | `no_mapping` | `2026-04-06 19:29:54.355` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003B5B8, sha=b003fe4f55c6`
  │ Windows Boot Manager|Status:|File:|No mapping|A733-EXC' | Select-Object -Last 80 | ForEach-Object { $_.Line }
- line 8323 | `bcd_0098` | `2026-04-06 19:29:54.355` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003B5B8, sha=b003fe4f55c6`
  File: \BCDStatus: 0xc0000098Info:                                                                                   [A733-TICK]
- line 8342 | `bcd_0098` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003B5B8, sha=b003fe4f55c6`
  │ 0xc0000098|File: \\BCD|File: \\EFI' -Context 3,3 | Select-Object -First 20 | ForEach-Object { '---'; $_.Context.PreContext;
- line 8407 | `bcd_0098` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003B5B8, sha=b003fe4f55c6`
  0xc0000098 の画面に入っていました。つまり 0x1003BB08 に届く前に screen helper 側へ吸われています。
- line 8409 | `live_sync` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003B5B8, sha=b003fe4f55c6`
  そのため方針を戻して、live の F:/EFI/BOOT/BOOTAA64.EFI と F:/EFI/Microsoft/Boot/bootmgfw.efi は今 0x1003BA54 -> NOP, 0x1003BA58 ->
- line 8422 | `no_mapping` | `2026-04-06 19:33:29.591` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003B5B8, sha=b003fe4f55c6`
  │ Windows Boot Manager|Status:|File:|No mapping|A733-EXC' | Select-Object -Last 80 | ForEach-Object { $_.Line }
- line 8496 | `no_mapping` | `2026-04-06 19:37:14.471` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003B5B8, sha=b003fe4f55c6`
  [2026-04-06 19:37:14.471] [A733-BOOT] Heartbeat 125 Event=23DC07118 Handle=23D2C0698 Base=23CCAB000 Started=1 Status=No mapping
- line 8498 | `no_mapping` | `2026-04-06 19:37:14.471` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003B5B8, sha=b003fe4f55c6`
  [2026-04-06 19:38:30.423] [A733-BOOT] Heartbeat 128 Event=23D162198 Handle=23D173F18 Base=23CB50000 Started=1 Status=No mapping
- line 8499 | `no_mapping` | `2026-04-06 19:38:30.423` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003B5B8, sha=b003fe4f55c6`
  [2026-04-06 19:38:30.425] [A733-BOOT] StartImage watch end Status=No mapping
- line 8517 | `no_mapping` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003B5B8, sha=b003fe4f55c6`
  • 今回の 0x1003BA6C 版は regression で、途中で No mapping に崩れています。安全に続けるため、まず既存 recipe に cleanup helper を飛ばし
- line 8517 | `regression` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003B5B8, sha=b003fe4f55c6`
  • 今回の 0x1003BA6C 版は regression で、途中で No mapping に崩れています。安全に続けるため、まず既存 recipe に cleanup helper を飛ばし
- line 8628 | `no_mapping` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003B5B8, sha=b003fe4f55c6`
  • 今回は deep stop に入らず、StartImage ... No mapping に崩れています。いまの live media が期待した patch 状態か、F: 上の loader 配置
- line 8660 | `no_mapping` | `timestamp-unknown` | marker: `nop_bootmgr_altpath_reporting_helper1_nop_bootmgr_altpath_screen_call_break_after_bootmgr_alt..., vas=0x1003BA54,0x1003BA58,0x1003BA6C, sha=42c041edca4a`
  • 原因候補はかなり狭まりました。いまの 0x1003BA6C 版で No mapping に崩れるなら、次は 0x101DE718 の cleanup helper 自体を飛ばして、その
- line 8661 | `safer` | `timestamp-unknown` | marker: `nop_bootmgr_altpath_reporting_helper1_nop_bootmgr_altpath_screen_call_break_after_bootmgr_alt..., vas=0x1003BA54,0x1003BA58,0x1003BA6C, sha=42c041edca4a`
  直後で止める safer 版に切り替えます。
- line 8680 | `safer` | `timestamp-unknown` | marker: `nop_bootmgr_altpath_reporting_helper1_nop_bootmgr_altpath_screen_call_break_after_bootmgr_alt..., vas=0x1003BA54,0x1003BA58,0x1003BA6C, sha=42c041edca4a`
  • 既存 recipe の並びは見えました。次は 0x1003BA64 の cleanup helper を NOP にして、0x1003BA68 か 0x1003BA6C で止める新しい safer 版を
- line 8699 | `no_mapping` | `timestamp-unknown` | marker: `nop_bootmgr_altpath_reporting_helper1_nop_bootmgr_altpath_screen_call_break_after_bootmgr_alt..., vas=0x1003BA54,0x1003BA58,0x1003BA6C, sha=42c041edca4a`
  • 次の版は source 側にも残るよう recipe を追加してから生成します。今回は 0x101DE718 を飛ばし、0x1003BA68 で止めるので、No mapping の原
- line 8769 | `live_sync` | `timestamp-unknown` | marker: `nop_bootmgr_altpath_reporting_helper1_nop_bootmgr_altpath_screen_call_break_after_bootmgr_alt..., vas=0x1003BA54,0x1003BA58,0x1003BA6C, sha=42c041edca4a`
  • 新しい variant 自体は生成できました。次は hash を取り直して、live の F:/EFI/BOOT/BOOTAA64.EFI と F:/EFI/Microsoft/Boot/bootmgfw.efi
- line 8816 | `no_mapping` | `timestamp-unknown` | marker: `nop_bootmgr_altpath_reporting_helper1_nop_bootmgr_altpath_screen_call_nop_bootmgr_altpath_cle..., vas=0x1003BA54,0x1003BA58,0x1003BA64,0x1003BA68, sha=55a92a809f47`
  • 今回の D:/Projects/PortaRe0/software/log/teraterm.log では、2026-04-06 19:38:30 JST に deep stop へ入らず StartImage ... No mapping
- line 8817 | `regression` | `timestamp-unknown` | marker: `nop_bootmgr_altpath_reporting_helper1_nop_bootmgr_altpath_screen_call_nop_bootmgr_altpath_cle..., vas=0x1003BA54,0x1003BA58,0x1003BA64,0x1003BA68, sha=55a92a809f47`
  へ崩れていました。いまの 0x1003BA6C 版だと、0x101DE718 の cleanup helper が本命の regression 候補です。
- line 8819 | `safer` | `timestamp-unknown` | marker: `nop_bootmgr_altpath_reporting_helper1_nop_bootmgr_altpath_screen_call_nop_bootmgr_altpath_cle..., vas=0x1003BA54,0x1003BA58,0x1003BA64,0x1003BA68, sha=55a92a809f47`
  そこで source の D:/Projects/porta-a733-bringup/build/patch_bootaa64.py に safer 版を追加して、live の F:/EFI/BOOT/BOOTAA64.EFI と
- line 8835 | `no_mapping` | `timestamp-unknown` | marker: `nop_bootmgr_altpath_reporting_helper1_nop_bootmgr_altpath_screen_call_nop_bootmgr_altpath_cle..., vas=0x1003BA54,0x1003BA58,0x1003BA64,0x1003BA68, sha=55a92a809f47`
  • 新しい run を確認します。まず D:/Projects/PortaRe0/software/log/teraterm.log の最終時刻と ELR / No mapping / Windows Boot Manager の
- line 8845 | `no_mapping` | `2026-04-06 19:48:28.570` | marker: `nop_bootmgr_altpath_reporting_helper1_nop_bootmgr_altpath_screen_call_nop_bootmgr_altpath_cle..., vas=0x1003BA54,0x1003BA58,0x1003BA64,0x1003BA68, sha=55a92a809f47`
  • Ran Select-String -Path 'D:\Projects\PortaRe0\software\log\teraterm.log' -Pattern 'ELR=|No mapping|Windows Boot Manager|Status:' |
- line 8998 | `no_mapping` | `timestamp-unknown` | marker: `nop_bootmgr_altpath_reporting_helper1_nop_bootmgr_altpath_screen_call_nop_bootmgr_altpath_cle..., vas=0x1003BA54,0x1003BA58,0x1003BA64,0x1003BAB0,0x1003BAB4, sha=ECC489529479`
  safer 版は効いていて、0x1003BA68 までは到達しました。ここで X23=0 だったので、次の分岐は 0x1003BAA4 側へ進むのが確定です。No mapping
- line 8998 | `safer` | `timestamp-unknown` | marker: `nop_bootmgr_altpath_reporting_helper1_nop_bootmgr_altpath_screen_call_nop_bootmgr_altpath_cle..., vas=0x1003BA54,0x1003BA58,0x1003BA64,0x1003BAB0,0x1003BAB4, sha=ECC489529479`
  safer 版は効いていて、0x1003BA68 までは到達しました。ここで X23=0 だったので、次の分岐は 0x1003BAA4 側へ進むのが確定です。No mapping
- line 9001 | `live_sync` | `timestamp-unknown` | marker: `nop_bootmgr_altpath_reporting_helper1_nop_bootmgr_altpath_screen_call_nop_bootmgr_altpath_cle..., vas=0x1003BA54,0x1003BA58,0x1003BA64,0x1003BAB0,0x1003BAB4, sha=ECC489529479`
  その先を見るために、live の F:/EFI/BOOT/BOOTAA64.EFI と F:/EFI/Microsoft/Boot/bootmgfw.efi は次の版へ更新済みです。今は
- line 9014 | `no_mapping` | `2026-04-06 19:55:14.442` | marker: `nop_bootmgr_altpath_reporting_helper1_nop_bootmgr_altpath_screen_call_nop_bootmgr_altpath_cle..., vas=0x1003BA54,0x1003BA58,0x1003BA64,0x1003BAB0,0x1003BAB4, sha=ECC489529479`
  • Ran Select-String -Path 'D:\Projects\PortaRe0\software\log\teraterm.log' -Pattern 'ELR=|No mapping|Windows Boot Manager|Status:' |

## Regression-Focused Notes

- line 4661 | `no_mapping` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA54,0x1003BA58,0x1003BA6C, sha=42c041edca4a`
  • 今回の run は shell からの chainload が別問題を起こしています。BOOTAA64.EFI 自体は見つかっていますが、StartImage が No mapping で落
- line 4672 | `no_mapping` | `2026-04-05 18:48:02.017` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA54,0x1003BA58,0x1003BA6C, sha=42c041edca4a`
  • Ran rg -n "No mapping|TESTA7Z|startup.nsh|bootmgfw\.efi|LoadImage|StartImage" 'D:\Projects\porta-a733-bringup' 'D:
- line 4686 | `no_mapping` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA54,0x1003BA58,0x1003BA6C, sha=42c041edca4a`
  • shell から BOOTAA64.EFI を直接叩くと StartImage failed: No mapping です。以前の導線メモ通り、ここは BootProbe/TESTA7Z 側を使うのが筋
- line 4714 | `no_mapping` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA54,0x1003BA58,0x1003BA6C, sha=42c041edca4a`
  • Ran rg -n "StartImage failed: No mapping|No mapping|startup.nsh|BOOTAA64.EFI" 'D:\Projects\PortaRe0\software\agents\PROGRESS.md' 'D:
- line 4773 | `no_mapping` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA54,0x1003BA58,0x1003BA6C, sha=42c041edca4a`
  • Ran rg -n "No mapping|EfiBootManagerBoot|LoadImage \(TRUE|LoadImage \(FALSE|BootPolicy|PlatformBootManagerAfterConsole entered" 'D:
- line 4823 | `no_mapping` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA54,0x1003BA58,0x1003BA6C, sha=42c041edca4a`
  • No mapping は診断用の LoadImage(TRUE) 経路が原因の可能性が高いです。なので、標準の EfiBootManagerBoot() 経路へ戻す差分を探して、その
- line 4881 | `no_mapping` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA54,0x1003BA58,0x1003BA6C, sha=42c041edca4a`
  • EfiBootManagerBoot() の API 定義は取れました。次は BootDevicePathOnce() を標準 boot option 化して、No mapping が消えるかを試します。
- line 5115 | `no_mapping` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA54,0x1003BA58,0x1003BA6C, sha=42c041edca4a`
  • この run は deep patch の続きではなく、loader 起動経路そのものがまた崩れています。No mapping と shell 側の探索失敗が同時に出ているの
- line 5128 | `no_mapping` | `2026-04-05 18:58:04.209` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA54,0x1003BA58,0x1003BA6C, sha=42c041edca4a`
  [2026-04-05 18:58:06.303] [A733-BOOT] Heartbeat 125 Event=23DC07118 Handle=23D2C0698 Base=23CCAB000 Started=1 Status=No mapping
- line 5145 | `no_mapping` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA54,0x1003BA58,0x1003BA6C, sha=42c041edca4a`
  • この run では deep path が途中で No mapping を返していて、前に追っていた 0x1003BA6C まで戻っていません。BCD と shell 側の launch 条
- line 5173 | `regression` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA54,0x1003BA58,0x1003BA6C, sha=42c041edca4a`
  • live の BCD 自体は生きていて、configaccesspolicy と custom:2600002a も入っています。なので、いまの regression は BCD 破損より launch
- line 5174 | `no_mapping` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA54,0x1003BA58,0x1003BA6C, sha=42c041edca4a`
  path 側の可能性が高いです。screen text が途中で出ているかどうかを見て、No mapping が表示経由の戻りなのか即エラーなのかを切ります。
- line 5321 | `no_mapping` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic...`
  の EfiBootManagerBoot() が F:/EFI/BOOT/BOOTAA64.EFI を起動し、18:58:06 に No mapping で返っています。その後 shell の F:/startup.nsh
- line 5322 | `no_mapping` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic...`
  も FS1:\EFI\Microsoft\Boot\bootmgfw.efi を見つけていますが、これも即 No mapping、さらに \EFI\BOOT\BOOTAA64.EFI を再実行しても最後は
- line 5323 | `no_mapping` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic...`
  No mapping でした。今回は ELR= も Windows Boot Manager 画面も出ていません。
- line 5336 | `no_mapping` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic...`
  • 新しい run で 0x1003B1F0 に戻れたか、それともまだ No mapping 側かを先に切ります。
- line 5362 | `no_mapping` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA54,0x1003BA58,0x1003B1F0, sha=5c8ccb4038bd`
  • いまの run で分岐は re-locate できました。0x1003B1F0 には戻れていて、No mapping 側ではなく、以前の success-path に復帰しています。次
- line 5439 | `no_mapping` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic...`
  • 今回の D:/Projects/PortaRe0/software/log/teraterm.log では、No mapping 側には落ちていません。2026-04-05 19:26:36 に狙い通り
- line 5878 | `no_mapping` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic...`
  理由は、いまはもう前半の No mapping や runtime 復帰そのものではなく、bootmgfw のかなり深い後段を追えているからです。最新では
- line 6223 | `no_mapping` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA54,0x1003BA58,0x1003BA6C, sha=42c041edca4a`
  • 今回の run は deep stop まで戻らず、StartImage ... No mapping に戻っています。まず shell fallback を確実に通すために、live の
- line 6295 | `no_mapping` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA54,0x1003BA58,0x1003BA6C, sha=42c041edca4a`
  • live の startup.nsh は修正済みです。direct boot の No mapping 自体はまだ残っていますが、次の run では shell fallback が fs4+ も拾え
- line 6314 | `no_mapping` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA54,0x1003BA58,0x1003BA6C, sha=42c041edca4a`
  • 今回の D:/Projects/PortaRe0/software/log/teraterm.log は deep stop には戻っていません。00:33:51 に StartImage ... No mapping で落ち
- line 6330 | `no_mapping` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA54,0x1003BA58,0x1003BA6C, sha=42c041edca4a`
  • 新しい run を見ます。fallback が通ったか、deep path に戻ったか、No mapping のままかをまず切ります。
- line 6346 | `no_mapping` | `2026-04-06 01:13:08.681` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA54,0x1003BA58,0x1003BA6C, sha=42c041edca4a`
  • Ran Select-String -Path 'D:\Projects\PortaRe0\software\log\teraterm.log' -Pattern 'No mapping|Windows Boot Manager|ELR=|not found on
- line 6349 | `no_mapping` | `2026-04-06 01:11:52.657` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA54,0x1003BA58,0x1003BA6C, sha=42c041edca4a`
  Base=23CCAB000 Started=1 Status=No mapping
- line 6403 | `no_mapping` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA54,0x1003BA58,0x1003BA6C, sha=42c041edca4a`
  • 今回の D:/Projects/PortaRe0/software/log/teraterm.log では、01:13:08 にまた StartImage ... No mapping で落ちて、その後 shell 側も
- line 6419 | `no_mapping` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA54,0x1003BA58,0x1003BA6C, sha=42c041edca4a`
  • 新しい run を見ます。current-volume fallback が効いたか、No mapping のままか、もしくは deep path に戻ったかを切ります。
- line 6428 | `no_mapping` | `2026-04-06 01:21:34.099` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA54,0x1003BA58,0x1003BA6C, sha=42c041edca4a`
  • Ran Select-String -Path 'D:\Projects\PortaRe0\software\log\teraterm.log' -Pattern 'No mapping|Windows Boot Manager|ELR=|not found on
- line 6431 | `no_mapping` | `2026-04-06 01:20:18.061` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA54,0x1003BA58,0x1003BA6C, sha=42c041edca4a`
  └ [2026-04-06 01:20:18.061] [A733-BOOT] Heartbeat 125 Event=23DC07118 Handle=23D2C0698 Base=23CCAB000 Started=1 Status=No mapping
- line 6432 | `no_mapping` | `2026-04-06 01:20:18.061` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA54,0x1003BA58,0x1003BA6C, sha=42c041edca4a`
  [2026-04-06 01:20:18.062] Error: Image at 0023CCAB000 start failed: No mapping
- line 6446 | `no_mapping` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA54,0x1003BA58,0x1003BA6C, sha=42c041edca4a`
  • 今回の regression は deep combined patch 側です。前に確実に通っていた 0x1003B49C 版へ一度戻して、まず No mapping から脱出します。
- line 6446 | `regression` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA54,0x1003BA58,0x1003BA6C, sha=42c041edca4a`
  • 今回の regression は deep combined patch 側です。前に確実に通っていた 0x1003B49C 版へ一度戻して、まず No mapping から脱出します。
- line 6487 | `no_mapping` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic...`
  • stable な 0x1003B49C 版へ戻しました。live の BOOT/bootmgfw と marker を揃えて、まず No mapping を消しにいきます。
- line 6504 | `no_mapping` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003B49C, sha=2be3653bb5a2`
  • 今回の D:/Projects/PortaRe0/software/log/teraterm.log では、01:21:34 にまた StartImage ... No mapping で落ちて、その後 shell も
- line 6506 | `regression` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003B49C, sha=2be3653bb5a2`
  ず、主因は deep combined patch 側の regression です。
- line 6512 | `no_mapping` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003B49C, sha=2be3653bb5a2`
  この SD で 1 回起動して、新しい D:/Projects/PortaRe0/software/log/teraterm.log をください。次はまず No mapping が消えて
- line 6522 | `no_mapping` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003B49C, sha=2be3653bb5a2`
  れたら、最近は StartImage ... No mapping に崩れて、bootmgfw 本体まで入れない run が混ざるようになりました。なので、まずは安定してい
- line 6523 | `no_mapping` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003B49C, sha=2be3653bb5a2`
  た 0x1003B49C 版へ戻して、No mapping を消して本流へ復帰させる段階です。
- line 6532 | `no_mapping` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003B49C, sha=2be3653bb5a2`
  • stable な 0x1003B49C 版へ戻した run を確認します。No mapping が消えたか、ELR=...649C に復帰したかをまず見ます。
- line 6548 | `no_mapping` | `2026-04-06 01:40:36.187` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003B49C, sha=2be3653bb5a2`
  • Ran Select-String -Path 'D:\Projects\PortaRe0\software\log\teraterm.log' -Pattern 'No mapping|Windows Boot Manager|ELR=|StartImage

## BCD-Focused Notes

- line 42 | `bcd_000d` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AF38, sha=f2d3da1b5fc7`
  0x101AEDB8 は success で返っています。なので BCD 0xc000000d の本体は、その次の success path 側です。
- line 328 | `bcd_000d` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003AFF4, sha=e2212c5940e9`
  • 新しい run を確認して、今回の patch が発火したかと BCD 0xc000000d の直前経路を見ます。
- line 3530 | `bcd_0098` | `2026-04-04 20:50:13.321` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BB08, sha=2a0a7c32488d`
  [2026-04-04 20:50:13.321] 13;001HFile: \BCDStatus: 0xc0000098Info:
- line 3570 | `bcd_0098` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BB08, sha=2a0a7c32488d`
  • この run は 0x1003BB08 に届かず、そのまま Windows Boot Manager / \BCD / 0xc0000098 画面に入っています。つまり前回の path は途中で変
- line 3616 | `bcd_0098` | `2026-04-05 00:22:18.004` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BAEC, sha=f1462e346740`
  [2026-04-05 00:22:18.004] File: \BCDStatus: 0xc0000098Info:
- line 3621 | `bcd_0098` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BAEC, sha=f1462e346740`
  • latest run は 0x1003BAEC を踏まずにそのまま 0xc0000098 画面へ行きました。いちばん筋がいい仮説は 0x1003B9F0 の loop-back なので、次は
- line 3641 | `bcd_0098` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BAEC, sha=f1462e346740`
  File: \BCD / Status: 0xc0000098 の画面に入っています。つまりこの run は 0x1003BAEC より前で別の枝を取っていて、そこが今の分岐点で
- line 3654 | `bcd_0098` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BAEC, sha=f1462e346740`
  • 最新の run と live の patch marker を見ます。まず 0x1003B9F0 に来たか、あるいは別枝で 0xc0000098 に落ちたかを確認します。
- line 3813 | `bcd_0098` | `2026-04-05 02:00:50.204` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BAEC, sha=f1462e346740`
  [2026-04-05 02:00:50.204] 1HFile: \BCDStatus: 0xc0000098Info:
- line 3934 | `bcd_0098` | `2026-04-05 02:08:15.909` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA5C, sha=12e69c309102`
  [2026-04-05 02:08:15.909] 1HFile: \BCDStatus: 0xc0000098Info:
- line 3980 | `bcd_0098` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA5C, sha=12e69c309102`
  \BCD / 0xc0000098 の画面に入っています。つまり 0x1003BA5C に到達する前に、直前の helper call が非復帰で screen path に入っている可能
- line 4013 | `bcd_0098` | `2026-04-05 02:12:59.571` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA58, sha=9bfdf4c1e3c0`
  [2026-04-05 02:12:59.571] 01HFile: \BCDStatus: 0xc0000098Info:
- line 4038 | `bcd_0098` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA58, sha=9bfdf4c1e3c0`
  \BCD / 0xc0000098 画面へ入っています。つまり bl 0x100451D8 の call site 自体には到達していません。
- line 4248 | `bcd_0098` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA54, sha=2a745364c37b`
  • Ran $m = Select-String -Path 'D:\Projects\PortaRe0\software\log\teraterm.log' -Pattern 'Windows Boot Manager|Status: 0xc0000098|
- line 4294 | `bcd_0098` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA54, sha=2a745364c37b`
  Status: 0xc0000098 でした。前の run では 2026-04-05 02:44:13 に ELR=0x23CCE7A54 が出ていて、0x1003BA54 の call site 直前までは来てい
- line 5181 | `bcd_0098` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA54,0x1003BA58,0x1003BA6C, sha=42c041edca4a`
  │ \BCD|File: \\EFI\\Microsoft\\Boot\\BCD|0xc0000098|0xc000000d' | Select-Object -Last 60 | ForEach-Object { $_.Line }
- line 5181 | `bcd_000d` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003BA54,0x1003BA58,0x1003BA6C, sha=42c041edca4a`
  │ \BCD|File: \\EFI\\Microsoft\\Boot\\BCD|0xc0000098|0xc000000d' | Select-Object -Last 60 | ForEach-Object { $_.Line }
- line 8270 | `bcd_0098` | `2026-04-06 19:27:13.497` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003B5B8, sha=b003fe4f55c6`
  assistance. File: \BCDStatus: 0xc0000098Info:
- line 8323 | `bcd_0098` | `2026-04-06 19:29:54.355` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003B5B8, sha=b003fe4f55c6`
  File: \BCDStatus: 0xc0000098Info:                                                                                   [A733-TICK]
- line 8342 | `bcd_0098` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003B5B8, sha=b003fe4f55c6`
  │ 0xc0000098|File: \\BCD|File: \\EFI' -Context 3,3 | Select-Object -First 20 | ForEach-Object { '---'; $_.Context.PreContext;
- line 8407 | `bcd_0098` | `timestamp-unknown` | marker: `skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolic..., vas=0x101B572C,0x101B67F4,0x1028DC58,0x101CC428,0x101AFA2C,0x1003AFEC,0x1003B3EC,0x1003B4B0,0x1003B5B8, sha=b003fe4f55c6`
  0xc0000098 の画面に入っていました。つまり 0x1003BB08 に届く前に screen helper 側へ吸われています。
