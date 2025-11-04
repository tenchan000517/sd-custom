# 高品質アニメイラスト生成ガイド

## 目標
元の写真から、商業レベルの高品質アニメイラストを生成する

**完成イメージ**: `C:\Users\tench\Downloads\11月号表紙_村上さん.png`
- セルアニメ調の高品質イラスト
- 明確な線画、柔らかい陰影
- 髪の光沢、瞳のハイライトなど細部まで精密
- 元のポーズと構図を維持

---

## 利用可能なリソース

### モデル
✅ **Counterfeit-V3.0** (9.4GB) - 高品質アニメモデル（推奨）
✅ **animagineXLV3_v30** (6.9GB) - SDXL アニメモデル（より高品質だが重い）
✅ **yayoiMix_v25** (2.1GB) - アニメ/リアルMix

### 拡張機能
✅ **ControlNet** - OpenPose & Canny利用可能（構図・ポーズ維持）
✅ **ADetailer** - 顔の高品質化
✅ **Simple Editor** - カスタムUI（改善可能）

---

## 方法1: 標準UIで高品質生成（推奨・すぐ試せる）

### ステップ1: WebUI起動と設定

```bash
cd /mnt/d/stable-diffusion-webui
python launch.py
```

ブラウザで `http://localhost:7860` にアクセス

### ステップ2: モデル選択

1. 画面上部のモデル選択ドロップダウンをクリック
2. **Counterfeit-V3.0.safetensors** を選択

### ステップ3: img2img設定

**img2img** タブに移動

#### 基本設定:
- **画像をアップロード**: 元の写真（`IMG_9104.jpeg`）
- **Resize mode**: Just resize（または Crop and resize）

#### プロンプト:
```
masterpiece, best quality, high quality, extremely detailed,
1girl, school uniform, black blazer, white shirt, red plaid necktie,
smiling, happy, ok sign, hand gesture,
anime style, cel shading, clean lineart,
detailed face, beautiful detailed eyes, glossy hair, shiny hair,
soft lighting, indoor background, professional illustration
```

#### ネガティブプロンプト:
```
lowres, bad anatomy, bad hands, text, error, missing fingers,
extra digit, fewer digits, cropped, worst quality, low quality,
normal quality, jpeg artifacts, signature, watermark, username,
blurry, artist name, photo, photorealistic, realistic,
3d render, sketch, unfinished
```

#### パラメータ:
- **Sampling method**: DPM++ 2M Karras（または Euler a）
- **Sampling steps**: 35-40
- **Width/Height**: 元画像のサイズを維持（または 512x768）
- **CFG Scale**: 7.5-9.0
- **Denoising strength**: 0.65-0.75

### ステップ4: ControlNet設定（重要！）

img2imgページの下部、**ControlNet** セクションを展開

#### Unit 0（OpenPose）:
- ✅ **Enable**: チェック
- **Preprocessor**: openpose_full
- **Model**: control_v11p_sd15_openpose_fp16
- **Control Weight**: 0.8-1.0
- **Starting Control Step**: 0
- **Ending Control Step**: 1.0

または

#### Unit 0（Canny）:
- ✅ **Enable**: チェック
- **Preprocessor**: canny
- **Model**: control_v11p_sd15_canny_fp16
- **Control Weight**: 0.6-0.8
- **Low threshold**: 100
- **High threshold**: 200

### ステップ5: ADetailer設定（オプションだが推奨）

**ADetailer** セクションを展開（img2imgページ下部）

- ✅ **Enable ADetailer**: チェック
- **ADetailer model**: face_yolov8n.pt（または mediapipe_face_full）
- **Prompt**: `beautiful detailed face, detailed eyes, glossy hair`
- **Negative prompt**: `bad face, bad eyes, bad anatomy`
- **Denoising strength**: 0.4-0.5

### ステップ6: 生成実行

**Generate** ボタンをクリック

⏱️ 処理時間: 30秒〜2分（GPU性能による）

### ステップ7: 結果の微調整

満足いかない場合：
- **Denoising strength** を調整（元の写真に近づける/離す）
- **CFG Scale** を調整（プロンプトへの従順度）
- **ControlNet weight** を調整（構図の保持度）
- **Seed** を変えて複数回生成

---

## 方法2: Simple Editorで生成（カスタムUI）

### 現在の制限
現在の Simple Editor は基本的な機能のみ。ControlNetやADetailerに対応していません。

### 使用方法

1. WebUI起動後、**かんたん編集** タブに移動
2. **スタイル変換** モード選択
3. 元の画像をアップロード
4. スタイル: **アニメ風** を選択
5. **詳細設定** を開く:
   - 変換の強さ: 0.65-0.75
   - 品質（ステップ数）: 35-40
6. **実行** ボタンをクリック

**注意**: この方法はControlNetを使わないため、ポーズや構図が変わる可能性があります。

---

## 方法3: Simple Editorの改善（推奨・長期的）

### 改善案

`/mnt/d/stable-diffusion-webui/extensions/simple-editor/scripts/unified_editor.py` を編集:

#### 1. 高品質アニメプリセットを追加

```python
STYLES = {
    # 既存のスタイル...

    # 追加
    "高品質アニメ": {
        "prompt": "masterpiece, best quality, high quality, extremely detailed, anime style, cel shading, clean lineart, detailed face, beautiful detailed eyes, glossy hair, shiny hair, soft lighting, professional illustration",
        "negative": "lowres, bad anatomy, bad hands, text, error, worst quality, low quality, jpeg artifacts, blurry, photo, photorealistic, realistic, 3d render, sketch, unfinished"
    },
}
```

#### 2. デフォルトパラメータを改善

```python
# 変更前
sampler_name="Euler a",
steps=20,
cfg_scale=7.0,

# 変更後
sampler_name="DPM++ 2M Karras",  # より高品質
steps=35,  # 品質向上
cfg_scale=8.0,  # プロンプトへの従順度アップ
```

#### 3. ControlNet統合（高度）

ControlNetの統合は複雑ですが、以下のようなアプローチが可能です：

```python
from modules.api.models import ControlNetUnit
import importlib

# ControlNet拡張の読み込み
try:
    external_code = importlib.import_module('extensions.sd-webui-controlnet.scripts.external_code', 'external_code')
    cn_available = True
except:
    cn_available = False

# 処理時にControlNetユニット追加
if cn_available:
    controlnet_unit = external_code.ControlNetUnit(
        enabled=True,
        module="openpose_full",
        model="control_v11p_sd15_openpose_fp16",
        weight=0.9,
    )
    p.script_args = [controlnet_unit]
```

---

## 推奨ワークフロー（ベストプラクティス）

### 初回生成:
1. **方法1**（標準UI + ControlNet + ADetailer）で生成
2. 結果を確認
3. パラメータを微調整して複数回試行

### 量産時:
1. Simple Editorを改善（上記の改善案を実装）
2. 最適なパラメータをデフォルト値に設定
3. カスタムUIで効率的に生成

---

## パラメータチューニングガイド

### Denoising Strength（変換の強さ）
- **0.5-0.6**: 元の写真に近い、写実的
- **0.65-0.75**: バランスが良い（推奨）
- **0.75-0.85**: アニメ化が強い
- **0.85-1.0**: 元の写真からかなり離れる

### CFG Scale
- **5.0-6.0**: 自由度が高い、ばらつきあり
- **7.0-8.0**: バランスが良い（推奨）
- **9.0-12.0**: プロンプトに忠実だが硬くなる
- **12.0+**: 過剰になる可能性

### Steps（ステップ数）
- **20**: 基本的な品質
- **30-35**: 良好な品質（推奨）
- **40-50**: 高品質だが時間がかかる
- **50+**: 改善効果が薄い

### ControlNet Weight
- **0.5-0.7**: ゆるく参照
- **0.8-0.9**: しっかり参照（推奨）
- **1.0**: 厳密に維持
- **1.0+**: 過剰に制約される可能性

---

## トラブルシューティング

### 生成されたイラストが元の写真と違いすぎる
→ **Denoising strength** を下げる（0.6前後）
→ **ControlNet** を有効化（OpenPose推奨）

### 顔の品質が低い
→ **ADetailer** を有効化
→ **Steps** を増やす（35-40）

### 生成に時間がかかりすぎる
→ **Steps** を減らす（25-30）
→ Sampler を Euler a に変更
→ 画像サイズを小さくする

### 構図やポーズが変わってしまう
→ **ControlNet** を必ず有効化
→ OpenPose の weight を 0.9-1.0 に設定

### VRAMが足りない
→ 画像サイズを512x768以下に縮小
→ Batch size を 1 に設定
→ `--medvram` または `--lowvram` で起動

---

## 完成度チェックリスト

高品質なアニメイラストの基準：

- ✅ **線画**: 明確で綺麗な線
- ✅ **陰影**: 柔らかく自然な影
- ✅ **目**: ハイライトがあり、詳細
- ✅ **髪**: 光沢があり、流れが自然
- ✅ **手**: 指が正確（ADetailerで手も検出可能）
- ✅ **ポーズ**: 元の写真と同じ
- ✅ **背景**: クリーンで整理されている
- ✅ **全体**: ノイズやアーティファクトがない

---

## 次のステップ

### すぐに試す:
1. **方法1**（標準UI）で元の写真を変換
2. 完成版と比較
3. パラメータを調整して再試行

### 効率化:
1. Simple Editor を改善
2. 最適な設定をプリセット化
3. バッチ処理を検討

### さらなる品質向上:
1. Hires.fix で高解像度化
2. 複数モデルを試す（animagineXLV3も試す価値あり）
3. LoRAモデルの活用を検討

---

**作成日**: 2025年11月4日
**対象**: Stable Diffusion WebUI + Counterfeit-V3.0
**目的**: 商業レベルの高品質アニメイラスト生成
