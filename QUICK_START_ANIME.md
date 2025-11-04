# 🚀 クイックスタート：高品質アニメイラスト生成

**目標**: 元の写真（IMG_9104.jpeg）を完成版のような高品質アニメイラストに変換する

---

## 最速で試す（10分）

### 1. WebUI起動

```bash
cd /mnt/d/stable-diffusion-webui
python launch.py
```

ブラウザで `http://localhost:7860` を開く

### 2. モデル選択

画面上部のドロップダウン → **Counterfeit-V3.0.safetensors** を選択

### 3. img2imgタブに移動

### 4. 画像アップロード

元の写真（`C:\Users\tench\Downloads\LINE WORKS\IMG_9104.jpeg`）をドラッグ&ドロップ

### 5. プロンプト入力

**Prompt**:
```
masterpiece, best quality, high quality, extremely detailed,
1girl, school uniform, black blazer, white shirt, red plaid necktie,
smiling, happy, ok sign, hand gesture,
anime style, cel shading, clean lineart,
detailed face, beautiful detailed eyes, glossy hair, shiny hair,
soft lighting, indoor background
```

**Negative prompt**:
```
lowres, bad anatomy, bad hands, worst quality, low quality,
blurry, photo, photorealistic, realistic, 3d render
```

### 6. パラメータ設定

- **Sampling method**: DPM++ 2M Karras
- **Sampling steps**: 35
- **CFG Scale**: 8.0
- **Denoising strength**: 0.70

### 7. ControlNet設定（重要！）

ページ下部の **ControlNet** セクションを展開

**Unit 0**:
- ✅ Enable にチェック
- **Preprocessor**: openpose_full
- **Model**: control_v11p_sd15_openpose_fp16
- **Control Weight**: 0.9

### 8. ADetailer設定（推奨）

ページ下部の **ADetailer** セクションを展開

- ✅ Enable ADetailer にチェック
- **ADetailer model**: face_yolov8n.pt
- **Prompt**: `beautiful detailed face, detailed eyes`
- **Denoising strength**: 0.4

### 9. 生成実行

**Generate** ボタンをクリック

⏱️ 待機: 30秒〜2分

### 10. 結果確認

生成されたイラストを確認。満足いかない場合は以下を調整：

- **より元の写真に近づける**: Denoising strength を 0.65 に下げる
- **よりアニメっぽくする**: Denoising strength を 0.75 に上げる
- **構図が変わった**: ControlNet weight を 1.0 に上げる
- **別のバリエーション**: Seed を変更して再生成

---

## 推奨パラメータまとめ

| パラメータ | 推奨値 | 説明 |
|-----------|--------|------|
| Model | Counterfeit-V3.0 | 高品質アニメモデル |
| Sampling method | DPM++ 2M Karras | 高品質サンプラー |
| Steps | 35-40 | 品質とスピードのバランス |
| CFG Scale | 7.5-8.5 | プロンプトへの従順度 |
| Denoising strength | 0.65-0.75 | 変換の強さ |
| ControlNet (OpenPose) | Weight 0.9 | ポーズ維持 |
| ADetailer | Enable | 顔の品質向上 |

---

## トラブルシューティング

### ポーズや構図が変わってしまう
→ ControlNet を必ず有効化
→ OpenPose の weight を 0.9-1.0 に

### 顔の品質が低い
→ ADetailer を有効化
→ Steps を 40 に増やす

### 元の写真と違いすぎる
→ Denoising strength を 0.6-0.65 に下げる

### 生成が遅い
→ Steps を 25-30 に減らす
→ 画像サイズを小さくする

---

## 次のステップ

### より詳しい情報:
`HIGH_QUALITY_ANIME_GUIDE.md` を参照

### カスタムUIで効率化:
Simple Editor の改善を検討（ガイド参照）

### さらなる品質向上:
- Hires.fix で高解像度化
- 別のモデル（animagineXLV3）も試す
- 複数回生成して最良のものを選ぶ

---

**作成日**: 2025年11月4日
