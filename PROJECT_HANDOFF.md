# 🤝 プロジェクト引き継ぎガイド

> **新しいClaude Codeインスタンスへ**: このドキュメントを最初に読んでください

## 📍 あなたがいる場所

**現在地**: `/mnt/c/sd-webui-analysis/`
**プロジェクト**: Stable Diffusion WebUI カスタマイズ
**状態**: 調査完了、カスタムUI実装済み、運用可能

## ⏱️ 5分で理解する

### プロジェクトの全体像

```
【やったこと】
Stable Diffusion WebUI (D:\stable-diffusion-webui) を完全調査
  ↓
システムアーキテクチャを完全理解
  ↓
詳細レポート作成（6件）
  ↓
カスタムUI「Simple Editor」を実装
  ↓
ドキュメント完備

【成果物】
1. 調査レポート: C:\sd-webui-analysis\*.md
2. カスタムUI: D:\stable-diffusion-webui\extensions\simple-editor\
```

### 実装した機能

**「かんたん編集」タブ**:
- 実写 → イラスト風変換（ワンクリック）
- 画像の部分編集（ブラシ + 自然言語指示）
- シンプルで直感的なUI

### すぐにやるべきこと

1. **README.md を読む** (このフォルダ)
2. **QUICKSTART.md の手順を試す** - 実装した機能を体験
3. **00_SUMMARY_REPORT.md を読む** - システム全体像

---

## 📂 ファイル構成マップ

### このフォルダ（C:\sd-webui-analysis\）

```
C:\sd-webui-analysis\
├── README.md                    ← プロジェクト全体の説明
├── PROJECT_HANDOFF.md          ← このファイル（引き継ぎ専用）
├── QUICKSTART.md               ← すぐ試せる手順
│
├── 00_SUMMARY_REPORT.md        ← 【重要】システム全体図、カスタマイズガイド
├── 01_project_overview.md      ← プロジェクト構造、ディレクトリマップ
├── 02_startup_flow.md          ← 起動フロー詳細
├── 03_shared_global_state.md   ← グローバル状態管理
├── 04_image_generation_pipeline.md  ← 画像生成パイプライン
└── 05_custom_ui_implementation_guide.md  ← カスタムUI実装方法
```

### 本体（D:\stable-diffusion-webui\）

```
D:\stable-diffusion-webui\
├── launch.py                   # エントリーポイント
├── webui.py                    # メインアプリケーション
├── modules\                    # コアモジュール（100+ファイル）
│   ├── shared.py              # ★ グローバル状態管理（最重要）
│   ├── processing.py          # ★ 画像生成コア
│   ├── ui.py                  # ★ UI構築
│   └── ...
│
├── extensions\                 # 拡張機能
│   └── simple-editor\         # ★ 今回実装したカスタムUI
│       ├── README.md
│       ├── install.py
│       └── scripts\
│           └── unified_editor.py  # メイン実装
│
├── models\                     # AIモデル保存場所
│   └── Stable-diffusion\      # SDモデル（.ckpt, .safetensors）
│
└── outputs\                    # 生成画像の保存先
```

---

## 🎯 開発タスク別ガイド

### ケース1: 実装した機能を改善したい

**対象**: `D:\stable-diffusion-webui\extensions\simple-editor\scripts\unified_editor.py`

**よくある変更**:

#### スタイルプリセットを追加
```python
# unified_editor.py の STYLES 辞書に追加
STYLES = {
    # ... 既存のスタイル ...

    "新しいスタイル": {
        "prompt": "your custom style description",
        "negative": "what to avoid"
    },
}
```

#### デフォルトパラメータを変更
```python
# StableDiffusionProcessingImg2Img のパラメータ
steps=20,          # 品質: 10-50
cfg_scale=7.0,     # CFGスケール: 5-15
sampler_name="Euler a",  # サンプラー変更可能
```

#### UI要素を追加
```python
# Gradio Blocks 内に追加
with gr.Row():
    new_component = gr.Slider(...)
```

**参考ドキュメント**: `05_custom_ui_implementation_guide.md`

---

### ケース2: 新しい機能を追加したい

**アプローチ**: 新しい拡張機能を作成

```bash
# 1. 新しい拡張機能フォルダ作成
mkdir -p /mnt/d/stable-diffusion-webui/extensions/my-extension/scripts

# 2. スクリプト作成
# extensions/my-extension/scripts/my_feature.py
```

**テンプレート**:
```python
import gradio as gr
import modules.script_callbacks as script_callbacks

def create_my_tab():
    with gr.Blocks() as ui:
        gr.Markdown("# My Feature")
        # UI構築...

    return [(ui, "マイ機能", "my_feature")]

script_callbacks.on_ui_tabs(create_my_tab)
```

**参考ドキュメント**: `05_custom_ui_implementation_guide.md`

---

### ケース3: コア機能を理解したい

**読むべきレポート**（優先順）:

1. **00_SUMMARY_REPORT.md** - システム全体図、アーキテクチャ
2. **04_image_generation_pipeline.md** - 画像生成の仕組み
3. **03_shared_global_state.md** - グローバル状態管理
4. **02_startup_flow.md** - 起動プロセス

**重要なファイル**:
```python
# グローバル状態
from modules.shared import state, opts, sd_model

# 画像生成
from modules.processing import StableDiffusionProcessingImg2Img, process_images

# UI構築
import gradio as gr
```

---

### ケース4: バグを修正したい

**デバッグ手順**:

1. **エラーメッセージを確認**
```bash
# WebUIのコンソール出力を確認
cd /mnt/d/stable-diffusion-webui
python launch.py
```

2. **ログを追加**
```python
# unified_editor.py に追加
print(f"Debug: input_image = {input_image}")
print(f"Debug: style = {style}")
```

3. **try-except で詳細情報取得**
```python
import traceback
try:
    # 処理
except Exception as e:
    print(f"Error: {e}")
    print(traceback.format_exc())
```

4. **よくあるエラー**
- モデル未読み込み → `shared.sd_model` を確認
- GPU メモリ不足 → `--lowvram` で起動
- 依存パッケージ不足 → `pip install -r requirements.txt`

---

## 🔑 重要な概念

### 1. グローバル状態管理

```python
from modules.shared import state, opts

# 処理状態
state.begin()           # 処理開始
state.job = "作業中..."  # ジョブ名設定
state.sampling_step = 5 # 進捗更新
state.end()             # 処理終了

# 設定
opts.cfg_scale          # 設定値取得
opts.save(filename)     # 設定保存
```

**詳細**: `03_shared_global_state.md`

### 2. 画像生成パイプライン

```python
from modules.processing import StableDiffusionProcessingImg2Img, process_images

# 処理オブジェクト生成
p = StableDiffusionProcessingImg2Img(
    sd_model=shared.sd_model,
    prompt="anime style",
    negative_prompt="photo",
    init_images=[image],
    denoising_strength=0.6,
    # ... その他のパラメータ
)

# 実行
processed = process_images(p)
result_image = processed.images[0]
```

**詳細**: `04_image_generation_pipeline.md`

### 3. UI構築

```python
import gradio as gr

with gr.Blocks() as ui:
    with gr.Row():
        input_img = gr.Image(type="pil")
        output_img = gr.Image(type="pil")

    btn = gr.Button("実行")
    btn.click(fn=my_function, inputs=[input_img], outputs=[output_img])
```

**詳細**: Gradio公式ドキュメント + `05_custom_ui_implementation_guide.md`

---

## 📋 チェックリスト

### 初日にやること

- [ ] README.md を読む
- [ ] QUICKSTART.md の手順を試す
- [ ] 実装した機能を実際に使ってみる
- [ ] 00_SUMMARY_REPORT.md でシステム全体を理解

### 開発開始前

- [ ] 対象ファイルの場所を確認
- [ ] 関連するレポートを読む
- [ ] バックアップを取る（git commit推奨）
- [ ] テスト環境で試す

### 開発中

- [ ] こまめにテスト
- [ ] エラーハンドリングを追加
- [ ] ログ出力を追加（デバッグ用）
- [ ] コメントを残す（日本語OK）

### 完了時

- [ ] 動作確認
- [ ] ドキュメント更新
- [ ] README.md に変更内容を記録
- [ ] git commit（推奨）

---

## 🆘 困ったときの対処法

### Q: どこから手をつけていいかわからない

**A**: 以下の順序で進めてください：

1. QUICKSTART.md → 実装した機能を体験（10分）
2. README.md → プロジェクト全体像（15分）
3. 00_SUMMARY_REPORT.md → システム理解（30分）
4. やりたいことに応じて詳細レポート参照

### Q: 特定の機能の実装方法がわからない

**A**: キーワードで検索：

```bash
# レポート内を検索
cd /mnt/c/sd-webui-analysis
grep -r "キーワード" *.md

# コード内を検索
cd /mnt/d/stable-diffusion-webui
grep -r "キーワード" modules/*.py
```

**よく検索するキーワード**:
- `StableDiffusionProcessing` - 画像生成
- `gr.Blocks` - UI構築
- `script_callbacks` - 拡張機能
- `shared.sd_model` - モデル参照

### Q: エラーが解決できない

**A**: 以下を確認：

1. **エラーメッセージをよく読む**
2. **ログを追加して原因特定**
3. **レポート内で類似の処理を探す**
4. **公式Wikiを確認**

### Q: パフォーマンスが悪い

**A**: 最適化手順：

1. `steps` を減らす（50 → 20）
2. `cfg_scale` を下げる（10 → 7）
3. `--xformers` で起動
4. `--lowvram` / `--medvram` を試す

---

## 📞 情報源

### プロジェクト内

- **C:\sd-webui-analysis\*.md** - すべてのレポート
- **D:\stable-diffusion-webui\extensions\simple-editor\README.md** - 実装した機能

### 外部リソース

- [AUTOMATIC1111 Wiki](https://github.com/AUTOMATIC1111/stable-diffusion-webui/wiki)
- [Gradio Docs](https://www.gradio.app/docs)
- [PyTorch Docs](https://pytorch.org/docs/)

### コミュニティ

- [GitHub Discussions](https://github.com/AUTOMATIC1111/stable-diffusion-webui/discussions)
- [Extensions Index](https://github.com/AUTOMATIC1111/stable-diffusion-webui-extensions)

---

## 🎓 学習パス

### 初心者（1日目）

1. システムを起動して使ってみる
2. 実装した機能を試す
3. README.md と 00_SUMMARY_REPORT.md を読む
4. 簡単な変更を試す（スタイル追加など）

### 中級者（1週間）

1. 全レポートを読む
2. 各モジュールのコードを読む
3. 新しいタブを実装してみる
4. 既存機能を改造してみる

### 上級者（1ヶ月〜）

1. コア機能の改造
2. 新しい生成モードの実装
3. パフォーマンス最適化
4. アーキテクチャ変更

---

## 📝 開発メモテンプレート

開発時はこのテンプレートを使ってメモを残してください：

```markdown
# 開発メモ: [機能名]

**日付**: YYYY-MM-DD
**開発者**: [あなたの名前/ID]

## 目的
何を実装/修正するか

## 変更箇所
- ファイル1: /path/to/file1.py
- ファイル2: /path/to/file2.py

## 変更内容
具体的に何を変更したか

## テスト結果
- [ ] 正常動作確認
- [ ] エラーハンドリング確認
- [ ] パフォーマンス確認

## 注意点
次の開発者への申し送り事項

## 参考資料
使ったレポートやドキュメント
```

---

## 🚀 次のステップ

### すぐにやること

1. **WebUIを起動**
```bash
cd /mnt/d/stable-diffusion-webui
./webui-user.bat  # または webui.sh
```

2. **新しいタブを確認**
- ブラウザで http://localhost:7860
- 「かんたん編集」タブをクリック

3. **機能を試す**
- スタイル変換を試す
- 部分編集を試す

### その後

4. **レポートを読む**
- 00_SUMMARY_REPORT.md で全体像把握
- 必要に応じて詳細レポート参照

5. **開発開始**
- 小さな変更から始める
- テストを繰り返す
- ドキュメントを更新

---

## ✅ 準備完了チェック

開発を始める前に、以下を確認：

- [ ] このファイル（PROJECT_HANDOFF.md）を読んだ
- [ ] README.md を読んだ
- [ ] QUICKSTART.md の手順を試した
- [ ] 実装した機能が動作することを確認した
- [ ] 00_SUMMARY_REPORT.md で全体像を理解した
- [ ] 開発環境（WebUI）が起動できる
- [ ] 必要なレポートの場所を把握した

すべてチェックできたら、開発開始の準備完了です！

---

**このドキュメントを読んだら、README.md を読んで、QUICKSTART.md を実行してください。**

**わからないことがあれば、まず該当するレポートを探してください。**

**すべての情報は、このフォルダ（C:\sd-webui-analysis\）にあります。**

---

**最終更新**: 2025年11月4日
**作成者**: Claude (Anthropic)
**次の開発者**: あなた！
