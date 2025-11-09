# キャラクター一貫性クイックリファレンス

**対象**: Stable Diffusion WebUIユーザー
**目的**: すぐに使えるパラメータ設定集

---

## 📋 基本設定テンプレート

### テンプレート1: 顔の一貫性（最高精度）

```
ControlNet Unit 1:
━━━━━━━━━━━━━━━━━━━━
Enable: ✓
Image: 顔のクローズアップ（512x512）
Preprocessor: ip-adapter-face-id-plus_sd15
Model: ip-adapter-plus-face_sd15.safetensors
Control Weight: 1.0
Starting Control Step: 0.0
Ending Control Step: 1.0
Control Mode: Balanced

プロンプトに追加:
<lora:ip-adapter-faceid-plusv2_sd15_lora:0.8>

期待される一貫性: 90-95%
```

### テンプレート2: 顔 + ポーズ制御

```
ControlNet Unit 1 (顔):
━━━━━━━━━━━━━━━━━━━━
Enable: ✓
Image: 顔参照画像
Preprocessor: ip-adapter-face-id-plus_sd15
Model: ip-adapter-plus-face_sd15.safetensors
Weight: 0.9
Start/End: 0.0 - 1.0

ControlNet Unit 2 (ポーズ):
━━━━━━━━━━━━━━━━━━━━
Enable: ✓
Image: ポーズ参照画像
Preprocessor: openpose_full
Model: control_v11p_sd15_openpose_fp16
Weight: 0.9
Start/End: 0.0 - 0.8

LoRA: <lora:ip-adapter-faceid-plusv2_sd15_lora:0.8>
```

### テンプレート3: 完全な構図維持（写真→アニメ）

```
img2img設定:
━━━━━━━━━━━━━━━━━━━━
Denoising strength: 0.70
Model: Counterfeit-V3.0
Sampler: DPM++ 2M Karras
Steps: 35
CFG: 7.0

ControlNet Unit 1 (元画像維持):
━━━━━━━━━━━━━━━━━━━━
Preprocessor: tile_resample
Model: control_v11f1e_sd15_tile_fp16
Weight: 0.7
Start/End: 0.0 - 1.0

ControlNet Unit 2 (輪郭維持):
━━━━━━━━━━━━━━━━━━━━
Preprocessor: canny
Model: control_v11p_sd15_canny_fp16
Weight: 0.5
Start/End: 0.0 - 1.0

ADetailer:
━━━━━━━━━━━━━━━━━━━━
Enable: ✓
Model: face_yolov8n.pt
Denoise: 0.4
```

### テンプレート4: 服装転送

```
ControlNet Unit 1 (顔維持):
━━━━━━━━━━━━━━━━━━━━
Image: キャラクター顔参照
Preprocessor: ip-adapter-face-id-plus_sd15
Model: ip-adapter-plus-face_sd15.safetensors
Weight: 1.0

ControlNet Unit 2 (服装転送):
━━━━━━━━━━━━━━━━━━━━
Image: 服装参照画像
Preprocessor: ip-adapter_sd15
Model: ip-adapter-plus_sd15.safetensors
Weight: 0.6
Start: 0.3, End: 0.8

プロンプト:
[キャラクター説明], wearing [服装詳細],
detailed clothing, fabric texture
<lora:ip-adapter-faceid-plusv2_sd15_lora:0.8>
```

---

## 🎯 パラメータ調整ガイド

### IP-Adapter Control Weight

| Weight | 一貫性 | 柔軟性 | 用途 |
|--------|--------|--------|------|
| 0.5-0.6 | 70% | 高 | 参考程度、多様性重視 |
| 0.7-0.8 | 80% | 中 | バランス良好 |
| 0.9-1.0 | 90% | 低 | Nano Banana相当 |
| 1.1-1.2 | 95% | 極低 | 最高精度 |

### LoRA強度

| 強度 | 効果 | 推奨用途 |
|------|------|----------|
| 0.3-0.5 | 弱 | 微調整、他のLoRAと併用 |
| 0.6-0.8 | 中 | **推奨（バランス最高）** |
| 0.9-1.0 | 強 | 一貫性最優先 |
| 1.1-1.5 | 過度 | 過学習気味の場合のみ |

### Denoising Strength（img2img）

| 強度 | 元画像維持 | 変化度 | 用途 |
|------|-----------|--------|------|
| 0.3-0.4 | 95% | 小 | 微調整、色補正 |
| 0.5-0.6 | 80% | 中 | スタイル軽変換 |
| 0.65-0.75 | 60% | 大 | **アニメ化（推奨）** |
| 0.8-0.9 | 40% | 極大 | 大幅変更 |

### CFG Scale

| CFG | プロンプト忠実度 | 創造性 | 推奨モデル |
|-----|-----------------|--------|------------|
| 3-5 | 低 | 高 | SDXL |
| 6-8 | 中 | 中 | **SD 1.5（推奨）** |
| 9-12 | 高 | 低 | 厳密な制御必要時 |
| 13+ | 過度 | なし | 非推奨 |

---

## 🚨 よくある問題と即効解決法

### 問題: 顔が毎回変わる

```
✗ 現在の設定:
  Weight: 0.5, LoRA: なし

✓ 修正案:
  Weight: 1.0
  LoRA: <lora:ip-adapter-faceid-plusv2_sd15_lora:0.8>
  CFG: 8.0
  Seed: 固定
```

### 問題: ポーズが反映されない

```
✗ 現在の設定:
  Preprocessor: openpose, Weight: 0.5

✓ 修正案:
  Preprocessor: openpose_full
  Weight: 0.9-1.0
  参照画像: 背景シンプル、1人のみ
  プレビュー確認: Preprocessorの出力を確認
```

### 問題: VRAM不足エラー

```
✗ 現在の設定:
  ControlNet: 3つ, Resolution: 768x1024

✓ 修正案1（ControlNet削減）:
  ControlNet: 2つまで（FaceID + OpenPose）
  Resolution: 512x768

✓ 修正案2（起動オプション）:
  --xformers --medvram --opt-sdp-attention

✓ 修正案3（ForgeWebUI）:
  Forge に移行（75%高速、低VRAM）
```

### 問題: 背景が変わってしまう

```
✗ 現在の設定:
  Denoising: 0.8, ControlNet: FaceIDのみ

✓ 修正案:
  Denoising: 0.6-0.7（低減）
  ControlNet追加: Tile (Weight 0.7)
  プロンプトで背景を明示
```

### 問題: 服装が参照と異なる

```
✗ 現在の設定:
  IP-Adapter Style, Weight: 0.4

✓ 修正案1（Weight調整）:
  Weight: 0.6-0.7
  Starting: 0.0（0.3から変更）

✓ 修正案2（Inpainting切替）:
  img2img → Inpaint
  服装部分をマスク
  Denoising: 0.75
  ControlNet: Canny（輪郭維持）
```

---

## 🎨 プロンプトテンプレート集

### アニメキャラクター（女性）

```
Positive:
masterpiece, best quality, 1girl,
[eye color] eyes, [hair length] [hair color] hair, [hairstyle],
[clothing description],
[pose/action], [expression],
detailed face, detailed eyes, soft lighting,
anime style, cel shading, vibrant colors
<lora:ip-adapter-faceid-plusv2_sd15_lora:0.8>

Negative:
lowres, bad anatomy, bad hands, bad face, bad eyes,
text, error, missing fingers, extra digit, fewer digits,
cropped, worst quality, low quality, normal quality,
jpeg artifacts, signature, watermark, username, blurry,
malformed face, mutation, deformed, ugly
```

### アニメキャラクター（男性）

```
Positive:
masterpiece, best quality, 1boy,
[eye color] eyes, [hair length] [hair color] hair,
[clothing description],
[pose/action], [expression],
detailed face, sharp features, cool lighting,
anime style, cel shading
<lora:ip-adapter-faceid-plusv2_sd15_lora:0.8>

Negative:
（女性版と同様）
```

### 写真→アニメイラスト変換

```
Positive:
masterpiece, best quality, highly detailed,
anime style illustration, cel shading, clean linework,
vibrant colors, soft gradients, detailed shading,
[元画像の内容説明],
professional anime artwork, studio quality

Negative:
photorealistic, photo, realistic, 3d render,
blurry, low quality, worst quality, bad anatomy,
noise, grain, jpeg artifacts
```

### 高品質ポートレート

```
Positive:
masterpiece, best quality, portrait,
1girl/1boy, [detailed character description],
beautiful detailed face, beautiful detailed eyes,
detailed hair, soft lighting, rim lighting,
depth of field, bokeh background,
professional illustration, high resolution
<lora:ip-adapter-faceid-plusv2_sd15_lora:0.8>

Negative:
lowres, bad anatomy, bad proportions,
bad hands, bad face, mutation, deformed,
ugly, worst quality, low quality, blurry
```

---

## 💻 RTX 5060 (8GB) 最適設定

### 起動コマンド

```batch
webui-user.bat の編集:

set COMMANDLINE_ARGS=--xformers --medvram --opt-sdp-attention --no-half-vae

説明:
--xformers          : メモリ効率化（必須）
--medvram           : 8GB向け最適化
--opt-sdp-attention : PyTorch 2.0高速化
--no-half-vae       : VAE精度問題回避
```

### Settings設定

```
Optimizations:
━━━━━━━━━━━━━━━━━━━━
✓ Use cross attention optimizations
✓ Use Xformers
CLIP skip: 2

VRAM Settings:
━━━━━━━━━━━━━━━━━━━━
✓ Unload VAE and CLIP from VRAM when training (for LORA)

ControlNet:
━━━━━━━━━━━━━━━━━━━━
✓ Low VRAM mode
✓ Use preprocessor output cache
Multi ControlNet: Max 2
```

### 推奨解像度（8GB）

| モデル | 推奨解像度 | ControlNet数 |
|--------|-----------|--------------|
| SD 1.5 | 512x768 | 2 |
| SD 1.5 + Upscale | 512→1024 | 1-2 |
| SDXL | 非推奨 | - |
| SSD-1B | 768x1024 | 1-2 |

### バッチ処理設定

```
Batch count: 1-4（順次生成）
Batch size: 1（同時生成は1のみ）
```

---

## 📊 手法比較早見表

### キャラクター一貫性手法

| 手法 | 一貫性 | VRAM | 速度 | 難易度 | 推奨度 |
|------|--------|------|------|--------|--------|
| IP-Adapter FaceID Plus V2 | 90% | 6GB | 速 | 中 | ★★★★★ |
| InstantID (SDXL) | 95% | 12GB | 中 | 中 | ★★★★☆ |
| PhotoMaker V2 | 92% | 10GB | 中 | 中 | ★★★★☆ |
| LoRA学習 | 95% | 8GB | 遅 | 高 | ★★★★☆ |
| DreamBooth | 97% | 12GB | 超遅 | 高 | ★★★☆☆ |

### アニメモデル比較（2025年版）

| モデル | スタイル | 品質 | サイズ | 初心者向け |
|--------|---------|------|--------|-----------|
| Counterfeit-V3.0 | バランス | ★★★★☆ | 2.1GB | ★★★★★ |
| Anything V5 | 汎用 | ★★★★★ | 2.1GB | ★★★★★ |
| MeinaMix | リアル寄り | ★★★★☆ | 2.1GB | ★★★★☆ |
| Pastel-Mix | ジブリ風 | ★★★★☆ | 2.0GB | ★★★★☆ |
| AOM3 | 映画的 | ★★★★★ | 2.1GB | ★★★☆☆ |

---

## 🔧 インストール必須リスト

### 最小構成（初心者向け）

```
✓ Forge WebUI または AUTOMATIC1111
✓ Counterfeit-V3.0 モデル
✓ ControlNet拡張（OpenPose, Canny）
✓ IP-Adapter FaceID Plus V2
✓ InsightFace（pip install）

推定インストール時間: 1-2時間
必要ディスク容量: 15GB
```

### 推奨構成（中級者向け）

```
上記 +
✓ ADetailer拡張
✓ Ultimate SD Upscale拡張
✓ ControlNet Depth, Tile モデル
✓ Anything V5, MeinaMix モデル

推定インストール時間: 2-3時間
必要ディスク容量: 25GB
```

### 完全構成（上級者向け）

```
上記 +
✓ InstantID モデル（SDXL用）
✓ PhotoMaker拡張（Forge）
✓ kohya_ss GUI（LoRA学習）
✓ AnimagineXL, SSD-1B モデル
✓ 複数アップスケーラー（R-ESRGAN, 4x-UltraSharp）

推定インストール時間: 4-6時間
必要ディスク容量: 50GB+
```

---

## 🚀 クイックスタート30分

### ステップ1: セットアップ（15分）

```
1. Forge WebUI ダウンロード・起動
   → 自動インストール完了

2. Counterfeit-V3.0 ダウンロード
   → models/Stable-diffusion/ に配置

3. IP-Adapter ダウンロード
   → models/ControlNet/ に配置:
     - ip-adapter-plus-face_sd15.safetensors

4. LoRA ダウンロード
   → models/Lora/ に配置:
     - ip-adapter-faceid-plusv2_sd15_lora.safetensors

5. InsightFace インストール
   → venv\Scripts\activate
   → pip install insightface
```

### ステップ2: 最初の生成（15分）

```
1. txt2img でキャラクター生成
   Model: Counterfeit-V3.0
   Prompt: masterpiece, 1girl, blue eyes, long blonde hair
   Size: 512x768, Steps: 30, CFG: 7

2. 顔をクロップ（512x512）

3. img2img で同じキャラクター再生成
   ControlNet:
   - Enable ✓
   - Image: クロップした顔
   - Preprocessor: ip-adapter-face-id-plus_sd15
   - Model: ip-adapter-plus-face_sd15
   - Weight: 0.9

   Prompt: <lora:ip-adapter-faceid-plusv2_sd15_lora:0.8>
            masterpiece, 1girl, different pose

4. 結果確認
   → 同じ顔で異なるポーズが生成されれば成功！
```

---

## 📞 トラブルシューティング連絡先

### 公式サポート

- **AUTOMATIC1111**: https://github.com/AUTOMATIC1111/stable-diffusion-webui/issues
- **Forge**: https://github.com/lllyasviel/stable-diffusion-webui-forge/issues
- **ControlNet**: https://github.com/Mikubill/sd-webui-controlnet/discussions

### コミュニティサポート

- **Reddit r/StableDiffusion**: 一般的な質問
- **Civitai Forums**: モデル・プロンプト関連
- **Discord Communities**: リアルタイムヘルプ

---

**最終更新**: 2025年11月9日
**バージョン**: 1.0
**次の更新予定**: API連携、ComfyUIワークフロー追加
