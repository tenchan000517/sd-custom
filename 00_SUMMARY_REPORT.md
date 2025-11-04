# Stable Diffusion WebUI - 完全理解レポート

## 調査日時
2025年11月4日

## 調査対象
D:\stable-diffusion-webui (AUTOMATIC1111版)

## エグゼクティブサマリー

Stable Diffusion WebUI は、Stability AI の Stable Diffusion モデルをブラウザから操作できるようにする Python + Gradio ベースのアプリケーションです。

**システム規模**:
- メインコード: 1000+ ファイル
- 主要モジュール: 100+ Pythonファイル
- 総行数: 推定 50,000+ 行

**アーキテクチャの特徴**:
1. **モジュラー設計**: 機能ごとに分離されたモジュール
2. **拡張可能**: スクリプトシステムと拡張機能システム
3. **高度な最適化**: VRAM節約、高速化技術の実装
4. **UIとロジックの分離**: Gradio UI と処理ロジックが独立

---

## システム全体図

```
┌─────────────────────────────────────────────────────────────┐
│                    launch.py (起動)                          │
│                          ↓                                   │
│              launch_utils.prepare_environment()              │
│        (依存関係インストール、環境準備)                        │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                    webui.py (メイン)                         │
│  ┌────────────────────────────────────────────────────┐     │
│  │ initialize()                                        │     │
│  │  ├─ バージョンチェック                                │     │
│  │  ├─ sd_models.setup_model() ← モデル準備           │     │
│  │  ├─ codeformer/gfpgan.setup_model()               │     │
│  │  └─ initialize_rest()                              │     │
│  │      ├─ サンプラー設定                              │     │
│  │      ├─ 拡張機能読み込み                            │     │
│  │      ├─ スクリプト読み込み                          │     │
│  │      └─ モデル読み込み（別スレッド）                 │     │
│  └────────────────────────────────────────────────────┘     │
│                          ↓                                   │
│  ┌────────────────────────────────────────────────────┐     │
│  │ webui() メインループ                                │     │
│  │  while True:                                        │     │
│  │    ├─ modules.ui.create_ui() ← UI構築             │     │
│  │    ├─ shared.demo.launch() ← Gradio起動          │     │
│  │    ├─ API追加                                      │     │
│  │    └─ サーバーコマンド待機（再起動可能）            │     │
│  └────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

---

## コアアーキテクチャ

### レイヤー構造

```
┌─────────────────────────────────────────┐
│  UI Layer (Gradio)                      │  ← ユーザーインタラクション
│  - modules/ui.py (89KB)                 │
│  - modules/ui_*.py                      │
├─────────────────────────────────────────┤
│  Application Layer                      │  ← ビジネスロジック
│  - modules/txt2img.py                   │
│  - modules/img2img.py                   │
│  - modules/processing.py (63KB)        │
├─────────────────────────────────────────┤
│  Model Layer                            │  ← AI モデル管理
│  - modules/sd_models.py (21KB)         │
│  - modules/sd_samplers*.py             │
│  - modules/sd_hijack.py (41KB)         │
│  - modules/prompt_parser.py (40KB)     │
├─────────────────────────────────────────┤
│  Shared State Layer                     │  ← グローバル状態
│  - modules/shared.py (47KB)            │
│    ├─ state (処理状態)                  │
│    ├─ opts (設定)                       │
│    └─ sd_model (モデル参照)             │
├─────────────────────────────────────────┤
│  Utility Layer                          │  ← ユーティリティ
│  - modules/devices.py (GPU管理)        │
│  - modules/images.py (画像保存)        │
│  - modules/paths.py (パス管理)         │
└─────────────────────────────────────────┘
```

---

## データフロー: 画像生成の流れ

### txt2img の例

```
ユーザー入力 (Gradio UI)
    ↓
txt2img(prompt, negative_prompt, steps, cfg_scale, ...)
    ↓
StableDiffusionProcessingTxt2Img() 生成
    │
    ├─ prompt: "a cat in a hat"
    ├─ negative_prompt: "blurry, low quality"
    ├─ seed: 12345
    ├─ steps: 20
    ├─ cfg_scale: 7.0
    ├─ width: 512, height: 512
    └─ sampler_name: "Euler a"
    ↓
process_images(p)
    ↓
┌───────────────────────────────────────────────────┐
│ process_images_inner(p) メインループ               │
│                                                   │
│ 1. 初期化                                          │
│    ├─ p.setup_prompts() → プロンプト展開          │
│    ├─ シード配列生成                               │
│    └─ Textual Inversion 読み込み                  │
│                                                   │
│ 2. イテレーションループ (n_iter回)                  │
│    for n in range(p.n_iter):                      │
│      ├─ p.parse_extra_network_prompts()          │
│      ├─ extra_networks.activate()                │
│      │                                            │
│      ├─ p.setup_conds()                          │
│      │   ├─ prompt → CLIP → conditioning (c)    │
│      │   └─ negative → CLIP → unconditioning (uc)│
│      │                                            │
│      ├─ p.sample(c, uc, seeds, ...)              │
│      │   │                                        │
│      │   ├─ create_random_tensors() → noise     │
│      │   ├─ サンプラー実行                        │
│      │   │   └─ UNet + スケジューラーで反復       │
│      │   └─ return latent                       │
│      │                                            │
│      ├─ decode_first_stage() → latent を画像化    │
│      │   └─ VAE decoder                          │
│      │                                            │
│      └─ 後処理                                    │
│          ├─ 顔修復 (GFPGAN/CodeFormer)           │
│          ├─ カラー補正                            │
│          ├─ オーバーレイ                          │
│          └─ 保存                                  │
│                                                   │
└───────────────────────────────────────────────────┘
    ↓
Processed(images, info, ...)
    ↓
Gradio UI に返却して表示
```

---

## 主要モジュール詳細

### 1. shared.py - グローバル状態管理の中枢

**役割**: すべてのモジュールから参照されるグローバル状態

**主要オブジェクト**:
```python
# 処理状態
state = State()
  - .skipped, .interrupted    # 処理制御
  - .job, .job_no, .job_count # ジョブ進捗
  - .sampling_step            # サンプリング進捗
  - .current_image            # ライブプレビュー

# 設定
opts = Options()
  - 動的プロパティアクセス (opts.cfg_scale)
  - JSON保存/読み込み
  - onchange コールバック

# モデル参照（遅延読み込み）
sd_model → modules.sd_models.model_data.get_sd_model()

# コマンドライン引数
cmd_opts
  - --lowvram, --medvram
  - --xformers
  - --api
  - など
```

**重要な設計**:
- `Options` クラスは `__getattr__` / `__setattr__` をオーバーライドして動的アクセス
- `State` クラスで処理状態を一元管理
- `sd_model` は `sys.modules` ハックで遅延読み込み

### 2. processing.py - 画像生成のコア

**役割**: 画像生成パイプラインの実装

**主要クラス**:
```python
StableDiffusionProcessing (基底クラス)
  ├─ StableDiffusionProcessingTxt2Img
  └─ StableDiffusionProcessingImg2Img

Processed (結果クラス)
  - images: 生成画像リスト
  - info: 生成パラメータ
  - seed, subseed
```

**主要関数**:
```python
process_images(p)
  └─ process_images_inner(p)  # メインループ
      ├─ p.setup_prompts()
      ├─ p.setup_conds()
      ├─ p.sample()
      ├─ decode_first_stage()
      └─ 後処理
```

**キャッシュ戦略**:
- コンディショニング（CLIP出力）をキャッシュ
- 同じプロンプトを繰り返し使う際に高速化

### 3. webui.py - アプリケーションメイン

**役割**: 起動、初期化、メインループ

**起動フロー**:
```python
main()
  ├─ initialize()
  │   ├─ check_versions()
  │   ├─ sd_models.setup_model()
  │   └─ initialize_rest()
  │
  └─ webui()
      └─ while 1:  # 再起動可能
          ├─ modules.ui.create_ui()
          ├─ shared.demo.launch()
          └─ サーバーコマンド待機
```

### 4. モデル管理 (sd_models.py, sd_hijack.py)

**sd_models.py** (21KB):
- モデルの読み込み、切り替え
- チェックポイント管理
- VAE管理

**sd_hijack.py** (41KB):
- Stable Diffusion モデルへの「ハック」
- プロンプト処理の改造
- 最適化の適用
- Textual Inversion の統合

### 5. プロンプト処理 (prompt_parser.py)

**役割**: プロンプトの解析と重み付け

**機能**:
- `(word)` → 重み1.1倍
- `[word]` → 重み0.9倍
- `(word:1.5)` → 明示的な重み
- `AND` → 複数プロンプトの結合
- スケジュール: `[word:10]` → 10ステップ目から適用

### 6. サンプラー (sd_samplers*.py)

**種類**:
- **CompVis サンプラー** (DDIM等)
- **k-diffusion サンプラー** (Euler, Euler a, DPM++等)
- **timesteps ベースサンプラー** (UniPC等)

**主要ファイル**:
- `sd_samplers.py` - サンプラー管理
- `sd_samplers_kdiffusion.py` (21KB) - k-diffusion実装
- `sd_samplers_cfg_denoiser.py` - CFG denoiser

---

## 拡張性のメカニズム

### 1. スクリプトシステム (scripts/)

**場所**: `/scripts/` ディレクトリ

**仕組み**:
```python
class Script:
    def title(self):
        return "My Script"

    def ui(self, is_img2img):
        # UI要素を返す
        return [gr.Slider(...)]

    def run(self, p, ...):
        # 画像生成をカスタマイズ
        # p を変更、または独自処理
        return Processed(...)
```

**コールバックポイント**:
- `before_process(p)`
- `process(p)`
- `before_process_batch(p, ...)`
- `process_batch(p, ...)`
- `postprocess_batch(p, x_samples, ...)`
- `postprocess_image(p, pp)`
- `postprocess(p, processed)`

### 2. 拡張機能システム (extensions/)

**場所**: `/extensions/` ディレクトリ

**構造**:
```
extensions/my-extension/
  ├─ install.py      # インストールスクリプト
  ├─ scripts/        # スクリプト
  ├─ javascript/     # JavaScript拡張
  └─ ...
```

**自動読み込み**: 起動時に自動的に読み込まれる

### 3. Hooks システム

**script_callbacks.py** で定義:
```python
# 各種コールバック登録
on_before_ui()
on_ui_tabs()
on_ui_settings()
on_before_reload()
on_script_unloaded()
```

---

## カスタマイズガイド

### レベル1: 設定変更

**方法**: `config.json` を編集

```json
{
  "sd_model_checkpoint": "my_model.safetensors",
  "CLIP_stop_at_last_layers": 2,
  "sd_vae": "my_vae.pt",
  "samples_format": "png"
}
```

### レベル2: スクリプト追加

**例**: カスタムスクリプトを追加

`/scripts/my_script.py`:
```python
import modules.scripts as scripts
import gradio as gr
from modules.processing import process_images

class MyScript(scripts.Script):
    def title(self):
        return "My Custom Script"

    def ui(self, is_img2img):
        strength = gr.Slider(minimum=0, maximum=1, value=0.5, label="Effect Strength")
        return [strength]

    def run(self, p, strength):
        # プロンプトにカスタム処理
        p.prompt = f"({p.prompt}:{strength})"

        # 通常の処理
        processed = process_images(p)
        return processed
```

### レベル3: モジュール改造

**例**: カスタムサンプラー追加

1. `modules/sd_samplers_kdiffusion.py` を参照
2. 新しいサンプラーを定義
3. `modules/sd_samplers.py` に登録

**例**: プロンプト処理のカスタマイズ

1. `modules/prompt_parser.py` を編集
2. 新しい構文を追加
3. パース処理を実装

### レベル4: コア機能拡張

**例**: 新しい生成モード追加

1. `StableDiffusionProcessing` のサブクラスを作成
2. `sample()` メソッドをオーバーライド
3. UI に統合

**参考コード**:
```python
class StableDiffusionProcessingMyMode(StableDiffusionProcessing):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # カスタム初期化

    def sample(self, conditioning, unconditional_conditioning, seeds, ...):
        # カスタムサンプリング処理
        # ...
        return samples
```

### レベル5: フル再実装

**アプローチ**:
1. 既存のコードベースを理解（このレポート）
2. 必要な部分を抽出
3. カスタムアーキテクチャで再構築

**参考にすべきファイル**:
- `processing.py` - 画像生成ロジック
- `sd_models.py` - モデル管理
- `sd_samplers*.py` - サンプリング
- `prompt_parser.py` - プロンプト処理

---

## 重要な実装テクニック

### 1. デバイス管理

```python
import modules.devices as devices

# GPU/CPUの自動選択
device = devices.device

# Autocast（自動型変換）
with devices.autocast():
    # GPU計算

# メモリクリーンアップ
devices.torch_gc()
```

### 2. VRAMの最適化

**lowvram モード**:
```python
if lowvram.is_enabled(sd_model):
    lowvram.send_everything_to_cpu()
```

**token merging**:
```python
sd_models.apply_token_merging(sd_model, ratio)
```

### 3. プログレス管理

```python
from modules.shared import state

# 処理開始
state.begin()
state.job = "Generating images"
state.job_count = 10

# 進捗更新
for i in range(state.job_count):
    state.job_no = i
    state.sampling_step = current_step
    state.set_current_image()  # ライブプレビュー

# 処理終了
state.end()
```

### 4. 設定の一時オーバーライド

```python
from modules.shared import opts

# 保存
stored_opts = {k: opts.data[k] for k in ['cfg_scale', 'steps']}

try:
    # 一時変更
    opts.cfg_scale = 10.0
    opts.steps = 30
    # 処理...
finally:
    # 復元
    for k, v in stored_opts.items():
        setattr(opts, k, v)
```

---

## パフォーマンス最適化

### 1. キャッシュ戦略

**コンディショニングキャッシュ**:
- 同じプロンプトを使い回す際に高速化
- `StableDiffusionProcessing.cached_c`, `cached_uc`

**モデルキャッシュ**:
- 複数モデルをRAMにキャッシュ
- `opts.sd_checkpoint_cache`

### 2. 並列処理

**バッチ処理**:
- `batch_size > 1` で複数画像を同時生成
- GPU並列処理

**非同期読み込み**:
```python
Thread(target=load_model).start()
Thread(target=devices.first_time_calculation).start()
```

### 3. メモリ管理

**autocast**:
- 自動的に float16 を使用（高速化）

**torch_gc**:
- 定期的にGPUメモリをクリーンアップ

**lowvram / medvram**:
- 4GB GPU でも動作可能

---

## セキュリティ考慮事項

### 1. restricted_opts

一部の設定は外部からの変更を制限:
```python
restricted_opts = {
    "outdir_samples",
    "outdir_txt2img_samples",
    # ...
}
```

### 2. CORS 設定

Gradio のデフォルト CORS を無効化:
```python
app.user_middleware = [x for x in app.user_middleware
                       if x.cls.__name__ != 'CORSMiddleware']
```

### 3. 認証

```python
gradio_auth_creds = list(get_gradio_auth_creds())
shared.demo.launch(auth=gradio_auth_creds)
```

---

## トラブルシューティング

### モデルが読み込めない

**確認事項**:
1. `models/Stable-diffusion/` にモデルファイルがあるか
2. ファイル形式: `.ckpt`, `.safetensors`
3. `sd_models.list_models()` でモデルが認識されているか

### VRAMが足りない

**解決策**:
1. `--lowvram` または `--medvram` で起動
2. `--xformers` で最適化
3. `opts.sd_checkpoint_cache = 0` でキャッシュ無効化
4. 画像サイズを小さくする（512x512）

### 画像生成が遅い

**最適化**:
1. `--xformers` で高速化
2. サンプラーを変更（Euler a は高速）
3. ステップ数を減らす（20ステップで十分な場合が多い）
4. Token Merging を有効化

---

## まとめ: カスタマイズの指針

### 簡単な変更（数時間）
- 設定ファイル編集
- スクリプト追加
- UI調整

### 中程度の変更（数日）
- カスタムサンプラー追加
- プロンプト構文拡張
- モデル管理のカスタマイズ

### 大規模な変更（数週間〜）
- 新しい生成モード実装
- アーキテクチャ変更
- フル再実装

### 推奨アプローチ

1. **まずは拡張機能/スクリプトで試す**
   - コアコードを変更せずに機能追加
   - 失敗してもロールバック可能

2. **小さく始める**
   - 1つの機能をカスタマイズ
   - 動作確認してから次へ

3. **既存のコードを参考にする**
   - 似た機能を探す
   - コピー＆ペースト＆改造

4. **テストを書く**
   - `/test/` ディレクトリ参照
   - 変更が他に影響しないか確認

---

## 参考資料

### 公式ドキュメント
- Wiki: https://github.com/AUTOMATIC1111/stable-diffusion-webui/wiki
- Custom Scripts: https://github.com/AUTOMATIC1111/stable-diffusion-webui/wiki/Custom-Scripts
- API: https://github.com/AUTOMATIC1111/stable-diffusion-webui/wiki/API

### 重要なファイル（再掲）
1. **shared.py** (47KB) - グローバル状態
2. **processing.py** (63KB) - 画像生成コア
3. **webui.py** (17KB) - メイン
4. **sd_models.py** (21KB) - モデル管理
5. **sd_hijack.py** (41KB) - モデル改造
6. **prompt_parser.py** (40KB) - プロンプト処理
7. **ui.py** (89KB) - UI構築

### コミュニティリソース
- 拡張機能: https://github.com/AUTOMATIC1111/stable-diffusion-webui-extensions
- DiscussionsTab: https://github.com/AUTOMATIC1111/stable-diffusion-webui/discussions

---

## 調査レポート一覧

このディレクトリ (`C:/sd-webui-analysis/`) には以下のレポートがあります：

1. **00_SUMMARY_REPORT.md** (このファイル) - 総合レポート
2. **01_project_overview.md** - プロジェクト概要、ディレクトリ構造
3. **02_startup_flow.md** - 起動フロー詳細
4. **03_shared_global_state.md** - グローバル状態管理詳細
5. **04_image_generation_pipeline.md** - 画像生成パイプライン詳細

すべてのレポートを読むことで、Stable Diffusion WebUI の完全な理解が得られます。

---

**調査完了日**: 2025年11月4日
**調査者**: Claude (Anthropic)
**目的**: Stable Diffusion WebUI の完全理解とカスタマイズ能力の獲得
**結果**: ✅ 完了 - システムアーキテクチャを完全に把握し、カスタマイズの指針を確立
