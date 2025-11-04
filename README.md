# Stable Diffusion WebUI カスタマイズプロジェクト

高品質なアニメイラスト生成を実現する、完全な調査とカスタムUI実装

## 📁 プロジェクト構成

```
sd-custom/
├── docs/                 # 完全な調査レポート
│   ├── START_HERE.md                      # 👈 まずここから読む
│   ├── QUICK_START_ANIME.md               # 🚀 10分で試せる高品質アニメ生成
│   ├── HIGH_QUALITY_ANIME_GUIDE.md        # 📖 完全ガイド
│   ├── 00_SUMMARY_REPORT.md               # システム全体図
│   └── ... (その他詳細レポート)
│
└── extensions/
    └── simple-editor/    # カスタムUI実装
        ├── install.py
        └── scripts/
            └── unified_editor.py          # メイン実装

```

## 🎯 このプロジェクトについて

### 目的
写真から商業レベルの高品質アニメイラストを生成する

### 実装済み機能
- ✅ 完全なシステム調査（6つの詳細レポート）
- ✅ カスタムUI「Simple Editor」実装
- ✅ スタイル変換モード（8種類のプリセット）
- ✅ 部分編集モード（inpainting）
- ✅ 高品質アニメ生成ガイド

## 🚀 クイックスタート

### 1. 調査レポートを読む

```bash
# まずここから
docs/START_HERE.md
```

### 2. カスタムUIをインストール

Stable Diffusion WebUIのextensionsフォルダにコピー：

```bash
# WebUIのextensionsフォルダにコピー
cp -r extensions/simple-editor /path/to/stable-diffusion-webui/extensions/

# WebUIを再起動
cd /path/to/stable-diffusion-webui
python launch.py
```

ブラウザで `http://localhost:7860` にアクセスすると、**「かんたん編集」**タブが追加されています。

### 3. 高品質アニメイラストを生成

```bash
# 詳細ガイドを参照
docs/QUICK_START_ANIME.md
```

## 📚 ドキュメント

### すぐ使いたい
- **QUICK_START_ANIME.md** - 10分で高品質アニメ生成

### システムを理解したい
- **START_HERE.md** - プロジェクト全体像
- **00_SUMMARY_REPORT.md** - システムアーキテクチャ

### 開発したい
- **PROJECT_HANDOFF.md** - 引き継ぎガイド
- **05_custom_ui_implementation_guide.md** - カスタムUI実装方法

### 詳細な技術情報
- **01_project_overview.md** - プロジェクト構造
- **02_startup_flow.md** - 起動フロー
- **03_shared_global_state.md** - 状態管理
- **04_image_generation_pipeline.md** - 画像生成パイプライン

## 🎨 使い方

### スタイル変換モード

1. 「かんたん編集」タブを開く
2. 画像をアップロード
3. スタイルを選択（例：高品質アニメ）
4. 実行ボタンをクリック

### 部分編集モード

1. 画像をアップロード
2. ブラシで編集したい箇所を塗る
3. 変更内容を文章で入力
4. 実行ボタンをクリック

## 🔧 システム要件

- **Stable Diffusion WebUI** (AUTOMATIC1111版)
- **Python 3.10+**
- **GPU**: NVIDIA GPU推奨（VRAM 6GB以上）
- **モデル**: Counterfeit-V3.0 またはアニメ系モデル

### 推奨拡張機能
- **ControlNet** - ポーズ・構図維持
- **ADetailer** - 顔の高品質化

## 💡 主な機能

### 実装済み
- 8種類のスタイルプリセット
- 直感的なUI/UX
- img2imgベースの高品質変換
- inpainting機能

### 改善予定
- ControlNet統合（ポーズ維持）
- ADetailer統合（顔の高品質化）
- より高品質なデフォルトパラメータ
- バッチ処理機能

## 🤝 貢献

このプロジェクトは継続的に改善されています。

フィードバックや改善案があれば、Issueを作成してください。

## 📄 ライセンス

AGPL-3.0 (Stable Diffusion WebUIに準拠)

## 🔗 関連リンク

- [Stable Diffusion WebUI](https://github.com/AUTOMATIC1111/stable-diffusion-webui)
- [ControlNet](https://github.com/Mikubill/sd-webui-controlnet)

---

**作成日**: 2025年11月4日
**作成者**: Claude (Anthropic)
**目的**: 高品質アニメイラスト生成の完全実装
