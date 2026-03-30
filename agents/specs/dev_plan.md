# ソフトウェア開発計画

> 決定日: 2026-03-17（session01）

---

## フレームワーク選定（確定）

| MCU | フレームワーク | 根拠 |
|-----|--------------|------|
| RP2040 #1（キーボード） | **QMK** | アナログスティック `pointing_device`、I2C BQ25895、ファンPWM、電源ボタン検出をカスタムタスクで実装可能。エコシステム・ドキュメントが最も充実。 |
| RP2040 #2（オーディオ） | **Pico SDK + TinyUSB** | USB Audio Class 2.0（UAC2）でLinux側ドライバ不要。PIO I2S MasterでMAX98357A/PCM5102Aに出力。 |

---

## RP2040 #1（QMK）実装内容

### キーマトリクス
- 9COL（GP0〜GP8）× 8ROW（GP9〜GP16）/ 63キー使用
- ダイオード方向: ROW → SW → COL（カソードがSW側）

### アナログスティック
- GP27（ADC1）= X、GP28（ADC2）= Y
- QMK `analog_joystick` + `pointing_device` でマウスとして動作

### BQ25895 I2C（LED制御）
- GP17（SCL）/ GP18（SDA）/ GP19（INT）
- カスタムタスクでI2Cポーリング → GP21(CHG橙) / GP22(FULL緑) / GP23(ACT青) 制御

### その他
- GP20: RP2040_EN（TPS61023 EN）
- GP24: USB_VBUS_EN
- GP25: 電源ボタン検出（10kΩ分圧）
- GP26: ファン PWM（BSS138 gate）

---

## RP2040 #2（Pico SDK + TinyUSB）実装内容

### 信号フロー
```
Cubie A7Z → VL812 DP4 → RP2040 #2（UAC2 USBオーディオ受信）
  → PIO I2S Master（GP0: BCLK / GP1: LRCLK / GP2: SDIN）
      ├─ MAX98357A × 2（U8: Left直結 / U15: 220kΩ=Right）→ スピーカー
      └─ PCM5102A → TPA6132A2 → 3.5mmジャック
```

### GPIO制御
| GPIO | 制御内容 |
|------|---------|
| GP3 | SD_MODE（スピーカーON/OFF） |
| GP4 | XSMT（PCM5102A ミュート） |
| GP5 | HP_EN（TPA6132A2 Enable） |
| GP6 | HP_DET割り込み → スピーカー/イヤホン自動切り替え |

### イヤホン/スピーカー切り替えロジック
- HP_DET HIGH（挿入）→ GP3=OFF（スピーカーミュート）/ GP4=ON（DACアクティブ）/ GP5=ON（HPアンプON）
- HP_DET LOW（未挿入）→ GP3=ON（スピーカーON）/ GP4=OFF（DACミュート）/ GP5=OFF（HPアンプOFF）

### Linux側
- UAC2準拠デバイスとして自動認識
- PipeWire / ALSA で追加ドライバ不要

---

## 開発順序（推奨）

1. **RP2040 #1 QMK** — キーマトリクス動作確認（スティック・LED後回しでもOK）
2. **RP2040 #2 TinyUSB UAC2** — USB Audio認識 → I2S出力確認
3. Linux側設定（ディスプレイ・SSD・USB HUB）

---

## 注意事項

- TinyUSB UAC2: サンプルレート/ビット深度設定とPIO I2Sのクロックドリフト対策が必要
- QMK RP2040: `GP_` プレフィックスの GPIO 名は `GP0` = `PAD_D0` マッピングに注意
