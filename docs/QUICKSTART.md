# 🚀 クイックスタートガイド

## すぐに使える！新しいUI

既にあなたのStable Diffusion WebUIに「**かんたん編集**」機能を追加しました！

### 📍 インストール場所

```
D:\stable-diffusion-webui\extensions\simple-editor\
  ├── install.py
  ├── README.md
  └── scripts\
      └── unified_editor.py
```

## ✨ 使い方（3ステップ）

### ステップ1: WebUIを起動

```bash
cd D:\stable-diffusion-webui
webui-user.bat
```

または既に起動している場合は**再起動**してください。

### ステップ2: 新しいタブを開く

ブラウザで `http://localhost:7860` にアクセスして、
**「かんたん編集」** タブをクリック！

### ステップ3: 使ってみる

#### 🎨 実写 → イラスト変換

1. 「スタイル変換」モードを選択
2. 実写画像をアップロード
3. 「アニメ風」を選択
4. 「✨ 実行」ボタンをクリック
5. 数秒〜数十秒で完成！

#### ✏️ 部分編集

1. 「部分編集」モードを選択
2. 画像をアップロード
3. ブラシで編集したい部分を白く塗る
4. 変更内容を入力（例: 「赤い帽子をかぶせて」）
5. 「✨ 実行」ボタンをクリック
6. 完成！

## 🎯 例題：やってみよう

### 例1: 自撮り写真をアニメ風に

```
モード: スタイル変換
画像: あなたの自撮り写真
スタイル: アニメ風
強さ: 0.6
実行！
```

### 例2: 風景写真をジブリ風に

```
モード: スタイル変換
画像: 風景写真
スタイル: ジブリ風
強さ: 0.7
実行！
```

### 例3: 人物写真の背景を変更

```
モード: 部分編集
画像: 人物写真
ブラシ: 背景部分を塗る
指示: 「夕焼けの海にして」
強さ: 0.8
実行！
```

### 例4: 表情を変える

```
モード: 部分編集
画像: 顔写真
ブラシ: 口元を塗る
指示: 「笑顔にして」
強さ: 0.6
実行！
```

## ⚙️ 設定のコツ

### 「強さ」の調整

- **0.3-0.5**: 元の画像に近い、微調整向け
- **0.5-0.7**: バランスが良い（推奨）
- **0.7-1.0**: 大きく変換、創造的

### 「品質」の調整

- **10-15**: 超高速、プレビュー用
- **20**: 標準、品質と速度のバランス（推奨）
- **30-50**: 高品質、時間がかかる

## 🔧 カスタマイズ

### スタイルを追加したい

`D:\stable-diffusion-webui\extensions\simple-editor\scripts\unified_editor.py` を開いて、

```python
STYLES = {
    # ... 既存のスタイル ...

    # ← ここに追加
    "あなたのスタイル": {
        "prompt": "your custom style, detailed description",
        "negative": "things to avoid"
    },
}
```

保存して再起動すると、新しいスタイルが選択できます！

### プロンプト例

**アニメスタイル**:
- `"anime style, studio quality, cel shading, vibrant colors"`
- `"manga style, detailed linework, professional"`

**絵画スタイル**:
- `"impressionist painting, monet style, soft brush strokes"`
- `"van gogh style, swirling brush strokes, vibrant"`

**その他**:
- `"cyberpunk style, neon lights, futuristic"`
- `"fantasy art, magical, ethereal, glowing"`

## 📚 さらに詳しく

すべての調査レポートは `C:\sd-webui-analysis\` にあります：

1. **00_SUMMARY_REPORT.md** - 総合レポート
2. **01_project_overview.md** - プロジェクト構造
3. **02_startup_flow.md** - 起動フロー
4. **03_shared_global_state.md** - 状態管理
5. **04_image_generation_pipeline.md** - 画像生成
6. **05_custom_ui_implementation_guide.md** - カスタムUI実装

## ❓ よくある質問

**Q: タブが表示されない**
A: WebUIを完全に再起動してください

**Q: エラーが出る**
A: モデルが読み込まれているか確認。`models/Stable-diffusion/` にモデルファイルがあるか確認

**Q: 遅い**
A: 「品質」を20→15に下げる、またはGPUを確認

**Q: 変換結果がおかしい**
A: 「強さ」を調整、または別のスタイルを試す

**Q: もっと高品質にしたい**
A: 「品質」を30-40に上げる、「強さ」を微調整

## 🎉 楽しんでください！

何か質問があれば、このレポートを参照してください。
あなたの創造性を存分に発揮してください！

---

**次のステップ**:
- [ ] WebUIを起動して試してみる
- [ ] 好きな画像で実験
- [ ] カスタムスタイルを追加
- [ ] さらに機能を拡張（レポート参照）
