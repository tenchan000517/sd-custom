# Stable Diffusion WebUI カスタマイズプロジェクト

## 📋 プロジェクト概要

このプロジェクトは、AUTOMATIC1111版 Stable Diffusion WebUI の完全な理解と、ユーザーフレンドリーなカスタムUI実装を目的としています。

**調査日**: 2025年11月4日
**対象システム**: D:\stable-diffusion-webui
**主な成果物**:
- 詳細な技術調査レポート（6件）
- カスタムUI拡張機能「Simple Editor」
- 完全なドキュメント

---

## 🎯 プロジェクトの目的

### 初期要件
1. **Stable Diffusion WebUIの完全理解**
   - システムアーキテクチャの把握
   - 起動フロー、画像生成パイプラインの理解
   - カスタマイズ可能性の調査

2. **カスタムシステムの開発能力獲得**
   - 独自の意図を盛り込んだシステムを作れるレベルの理解
   - 拡張機能・カスタムUIの実装方法習得

### 実装した機能
1. **実写画像をイラスト風に変換** (img2img + スタイルプリセット)
2. **画像の部分編集** (inpainting + 自然言語指示)
3. **シンプルで直感的なUI** (既存UIは複雑すぎるため)

---

## 📁 ディレクトリ構造

```
プロジェクト関連ファイル
├── C:\sd-webui-analysis\          # 調査レポート（このフォルダ）
│   ├── README.md                   # このファイル（プロジェクトの全体像）
│   ├── PROJECT_HANDOFF.md          # 引き継ぎガイド
│   ├── QUICKSTART.md               # クイックスタート
│   ├── 00_SUMMARY_REPORT.md        # 総合レポート
│   ├── 01_project_overview.md      # プロジェクト構造
│   ├── 02_startup_flow.md          # 起動フロー
│   ├── 03_shared_global_state.md   # グローバル状態管理
│   ├── 04_image_generation_pipeline.md  # 画像生成パイプライン
│   └── 05_custom_ui_implementation_guide.md  # カスタムUI実装
│
└── D:\stable-diffusion-webui\      # 本体
    ├── launch.py                   # エントリーポイント
    ├── webui.py                    # メインアプリケーション
    ├── modules\                    # コアモジュール（最重要）
    │   ├── shared.py               # グローバル状態管理（47KB）
    │   ├── processing.py           # 画像生成コア（63KB）
    │   ├── ui.py                   # UI構築（89KB）
    │   └── ... (100+ ファイル)
    │
    └── extensions\                 # 拡張機能
        └── simple-editor\          # ★ 今回実装したカスタムUI
            ├── README.md
            ├── install.py
            └── scripts\
                └── unified_editor.py  # メイン実装（11KB）
```

---

## 🚀 クイックスタート

### 新しいClaude Codeインスタンスへ

1. **このREADMEを読む** (5分)
2. **00_SUMMARY_REPORT.md を読む** (15分) - システム全体像を把握
3. **QUICKSTART.md の手順を試す** (10分) - 実装した機能を体験
4. **必要に応じて詳細レポートを参照**

### 開発を継続する場合

```bash
# 1. 対象システムに移動
cd /mnt/d/stable-diffusion-webui

# 2. 既存の拡張機能を確認
ls extensions/simple-editor/

# 3. 調査レポートを参照
cd /mnt/c/sd-webui-analysis/
ls -la
```

---

## 📊 システムアーキテクチャ要約

### レイヤー構造

```
┌─────────────────────────────────┐
│  UI Layer (Gradio)              │ ← modules/ui.py
├─────────────────────────────────┤
│  Application Layer              │ ← txt2img.py, img2img.py
│  (ビジネスロジック)               │    processing.py
├─────────────────────────────────┤
│  Model Layer                    │ ← sd_models.py
│  (AI モデル管理)                 │    sd_samplers.py
├─────────────────────────────────┤
│  Shared State Layer             │ ← shared.py
│  (グローバル状態)                 │
├─────────────────────────────────┤
│  Utility Layer                  │ ← devices.py, images.py
└─────────────────────────────────┘
```

### 画像生成フロー

```
UI入力
  ↓
txt2img() / img2img()
  ↓
StableDiffusionProcessing 生成
  ↓
process_images()
  ├─ setup_prompts()      # プロンプト準備
  ├─ setup_conds()        # CLIP処理
  ├─ sample()             # サンプリング（ノイズ除去）
  ├─ decode_first_stage() # VAEデコード
  └─ 後処理（顔修復、保存）
  ↓
Processed オブジェクト
  ↓
UI表示
```

### 重要なファイル（優先度順）

1. **shared.py** (47KB) - グローバル状態、設定、モデル参照
2. **processing.py** (63KB) - 画像生成のコア
3. **webui.py** (17KB) - 起動、初期化
4. **ui.py** (89KB) - UI構築
5. **sd_models.py** (21KB) - モデル管理
6. **prompt_parser.py** (40KB) - プロンプト処理

---

## 🔧 実装済み機能

### Simple Editor 拡張機能

**場所**: `D:\stable-diffusion-webui\extensions\simple-editor\`

**機能**:

#### 1. スタイル変換モード
- 実写 → アニメ風
- 実写 → 水彩画風
- 実写 → 油絵風
- 実写 → ジブリ風
- 実写 → ピクサー風
- など8種類のプリセット

#### 2. 部分編集モード
- ブラシで編集箇所を選択
- 自然言語で変更内容を指示
- 自動で部分的に編集

**実装方法**:
- Gradio Blocks でカスタムUI
- 既存の `StableDiffusionProcessingImg2Img` を活用
- `script_callbacks.on_ui_tabs()` でタブ登録

**コード**: `extensions/simple-editor/scripts/unified_editor.py` (11KB)

---

## 💻 技術スタック

### 言語・フレームワーク
- **Python 3.10.6**
- **Gradio 3.32.0** - WebUIフレームワーク
- **PyTorch 2.0+** - ディープラーニング
- **Transformers 4.25.1** - CLIP等

### 主要ライブラリ
- **diffusers** - Diffusionモデル
- **accelerate** - PyTorch高速化
- **safetensors** - モデル保存形式
- **opencv, PIL, numpy** - 画像処理

---

## 📖 ドキュメント一覧

### 調査レポート（C:\sd-webui-analysis\）

1. **00_SUMMARY_REPORT.md** (22KB)
   - システム全体図
   - アーキテクチャ解説
   - カスタマイズガイド（5段階）
   - トラブルシューティング

2. **01_project_overview.md** (9.6KB)
   - ディレクトリ構造の完全マップ
   - 主要ファイル一覧
   - 依存ライブラリ

3. **02_startup_flow.md** (14KB)
   - launch.py → webui.py の詳細
   - 初期化プロセス
   - 再起動可能な設計

4. **03_shared_global_state.md** (17KB)
   - shared.py の完全解析
   - State, Options クラス
   - 設定システム

5. **04_image_generation_pipeline.md** (30KB)
   - processing.py の完全解析
   - txt2img / img2img 実装
   - サンプリングからデコードまで

6. **05_custom_ui_implementation_guide.md**
   - カスタムUI実装の手順
   - コード例付き
   - 拡張方法

### 実装ドキュメント

- **QUICKSTART.md** - すぐに使えるガイド
- **PROJECT_HANDOFF.md** - 引き継ぎ専用ガイド（このファイル用）

---

## 🛠️ 開発ガイド

### 簡単なカスタマイズ（1-2時間）

**新しいスタイルプリセット追加**:

`extensions/simple-editor/scripts/unified_editor.py` を編集：

```python
STYLES = {
    # 既存のスタイル...

    # 追加
    "新しいスタイル": {
        "prompt": "your style description here",
        "negative": "things to avoid"
    },
}
```

### 中級カスタマイズ（1-2日）

**新しいタブ追加**:

```python
# extensions/my-extension/scripts/my_tab.py
import gradio as gr
import modules.script_callbacks as script_callbacks

def create_my_tab():
    with gr.Blocks() as ui:
        gr.Markdown("# My Custom Tab")
        # UI構築...

    return [(ui, "マイタブ", "my_tab")]

script_callbacks.on_ui_tabs(create_my_tab)
```

### 上級カスタマイズ（数週間）

**コア機能の改造**:

1. `modules/` 内のファイルを編集
2. 既存のクラスを継承
3. 新しい処理パイプライン実装

詳細は `04_image_generation_pipeline.md` 参照。

---

## 🐛 トラブルシューティング

### よくある問題

**Q: 拡張機能が読み込まれない**
```bash
# 解決策
1. WebUIを完全に再起動
2. extensions/simple-editor/ の存在確認
3. install.py が実行されているか確認
```

**Q: エラーが出る**
```bash
# 確認事項
1. モデルが正しく読み込まれているか
2. CUDA/GPU が利用可能か
3. 依存パッケージがインストールされているか
```

**Q: 変換結果が期待と違う**
```bash
# 調整
1. "強さ" スライダーを変更
2. "品質" (ステップ数) を調整
3. 別のスタイルを試す
```

### デバッグ方法

**ログ確認**:
```bash
# コンソール出力を確認
python launch.py --log-level DEBUG
```

**エラートレース**:
```python
# unified_editor.py に追加
import traceback
try:
    # 処理
except Exception as e:
    print(traceback.format_exc())
```

---

## 🔄 次のステップ

### 推奨される開発順序

1. **まず使ってみる** (30分)
   - QUICKSTART.md に従って動作確認
   - 各機能を実際に試す

2. **アーキテクチャを理解** (1-2時間)
   - 00_SUMMARY_REPORT.md を熟読
   - システム全体図を把握

3. **簡単なカスタマイズ** (数時間)
   - スタイルプリセット追加
   - UI調整

4. **本格的な機能追加** (数日〜)
   - 新しいタブ実装
   - 独自処理ロジック

### 開発アイデア

**UI改善**:
- [ ] Before/After比較スライダー
- [ ] バッチ処理機能
- [ ] プリセット保存機能
- [ ] 履歴機能

**機能追加**:
- [ ] 動画対応
- [ ] 自動マスク生成（AIベース）
- [ ] LoRAサポート
- [ ] リアルタイムプレビュー

**最適化**:
- [ ] キャッシュ機能強化
- [ ] 並列処理
- [ ] モバイル対応

---

## 📚 参考資料

### 公式リソース
- [AUTOMATIC1111 Wiki](https://github.com/AUTOMATIC1111/stable-diffusion-webui/wiki)
- [Custom Scripts Guide](https://github.com/AUTOMATIC1111/stable-diffusion-webui/wiki/Custom-Scripts)
- [API Documentation](https://github.com/AUTOMATIC1111/stable-diffusion-webui/wiki/API)

### コミュニティ
- [Extensions Index](https://github.com/AUTOMATIC1111/stable-diffusion-webui-extensions)
- [Discussions](https://github.com/AUTOMATIC1111/stable-diffusion-webui/discussions)

### 技術情報
- Stable Diffusion: https://github.com/Stability-AI/stablediffusion
- Gradio: https://www.gradio.app/docs
- PyTorch: https://pytorch.org/docs/

---

## 📝 ノート

### 設計判断

**なぜ拡張機能として実装？**
- コアコードを変更しない
- アップデートの影響を受けにくい
- 独立してメンテナンス可能
- 簡単に有効/無効化できる

**なぜGradio Blocks？**
- 柔軟なレイアウト
- カスタムUIが作りやすい
- 既存システムとの統合が容易

**なぜimg2imgベース？**
- 既存の高品質な実装を活用
- 車輪の再発明を避ける
- メンテナンスコスト削減

### 学んだこと

1. **モジュラー設計の重要性**
   - 機能ごとに分離
   - 依存関係を最小化
   - テストしやすい構造

2. **拡張性の重要性**
   - コールバックシステム
   - プラグイン機構
   - 設定システム

3. **ユーザビリティ第一**
   - シンプルなUI
   - 直感的な操作
   - わかりやすいエラーメッセージ

---

## 👥 貢献者

**初期調査・実装**: Claude (Anthropic) - 2025年11月4日

**今後の開発者へ**:
このドキュメントを読んでいるあなたが、次の貢献者です。
わからないことがあれば、各レポートを参照してください。
すべての情報はこのフォルダにあります。

---

## 📄 ライセンス

このカスタマイズは、AUTOMATIC1111 Stable Diffusion WebUIのライセンス（AGPL-3.0）に準拠します。

---

## 🔗 クイックリンク

- **すぐ使いたい**: `QUICKSTART.md`
- **引き継ぎたい**: `PROJECT_HANDOFF.md`
- **システム理解**: `00_SUMMARY_REPORT.md`
- **実装方法**: `05_custom_ui_implementation_guide.md`

---

**最終更新**: 2025年11月4日
**バージョン**: 1.0
**ステータス**: 完成、運用可能
