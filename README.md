# porta-a733-bringup

A733 の Linux/Windows bring-up、boot media 生成、調査ログを切り出した repo です。

## 含めたもの

- Linux / Windows installer 配置 script
- vendor Linux 起動 script
- 調査メモ
- serial log
- vendor boot asset 抽出結果のうち小さいもの

## 含めていないもの

- 大きい raw image / ISO
  - vendor rootfs raw image
  - Ubuntu ISO
- 一時展開ディレクトリ
- build 出力物

## 既知の基準点

- vendor Linux userspace 到達
- `xorg-direct` 経路で HDMI 出力成立
- capture 互換 mode の基準点:
  - `runid=20260330-212118`
  - `forced-mode=1920x1080@60`
  - `xsetroot-ok`

## 補足

`build/install_radxa_vendor_linux.py` の既定値は `roms/_work/radxa-cubie-a7z_bullseye_kde_b1.output_512.img` を前提にしています。この大きい raw image はこの repo にはコピーしていません。
