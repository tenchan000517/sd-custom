# Stable Diffusion WebUI - shared.py グローバル状態管理

## 概要

`shared.py` は Stable Diffusion WebUI の心臓部であり、アプリケーション全体で共有されるグローバル状態、設定、オプション、モデル参照を管理します。

**ファイルサイズ**: 47KB (非常に大きい）
**役割**: 中央集権的な状態管理
**重要度**: ★★★★★ （最重要ファイルの一つ）

## 主要なグローバル変数

### 1. `demo` - Gradio アプリケーション
```python
demo = None  # Gradio app インスタンス
```
- `modules.ui.create_ui()` で作成されたGradioアプリケーション
- `webui.py` から参照される

### 2. `cmd_opts` - コマンドライン引数
```python
parser = cmd_args.parser
cmd_opts = parser.parse_args()
```
起動時のコマンドライン引数を保持：
- `--lowvram`, `--medvram`: VRAM節約モード
- `--xformers`: メモリ最適化
- `--api`: REST API有効化
- `--share`: Gradio共有リンク
- その他多数

### 3. `state` - 処理状態管理（State クラス）

`/mnt/d/stable-diffusion-webui/modules/shared.py:90-223`

```python
class State:
    # 処理制御
    skipped = False          # スキップフラグ
    interrupted = False      # 中断フラグ

    # ジョブ管理
    job = ""                 # 現在のジョブ名
    job_no = 0               # 現在のジョブ番号
    job_count = 0            # 総ジョブ数
    job_timestamp = '0'      # ジョブのタイムスタンプ

    # サンプリング進捗
    sampling_step = 0        # 現在のサンプリングステップ
    sampling_steps = 0       # 総サンプリングステップ数

    # プレビュー関連
    current_latent = None              # 現在の潜在表現
    current_image = None               # 現在のプレビュー画像
    current_image_sampling_step = 0    # 最後にプレビューを更新したステップ
    id_live_preview = 0                # プレビューID（更新検知用）

    # その他
    textinfo = None          # テキスト情報
    time_start = None        # 処理開始時刻
    server_start = None      # サーバー起動時刻
```

#### State クラスの主要メソッド

**サーバーコマンド管理**:
```python
def wait_for_server_command(timeout=None):
    """再起動や停止のコマンドを待機"""
    # webui.py のメインループから呼ばれる

def request_restart():
    """再起動をリクエスト"""
    self.interrupt()
    self.server_command = "restart"
```

**処理制御**:
```python
def skip():
    """現在の処理をスキップ"""
    self.skipped = True

def interrupt():
    """現在の処理を中断"""
    self.interrupted = True

def begin():
    """処理開始時の初期化"""
    self.sampling_step = 0
    self.job_count = -1
    # ... その他の初期化
    devices.torch_gc()  # GPU メモリクリーンアップ

def end():
    """処理終了時のクリーンアップ"""
    self.job = ""
    self.job_count = 0
    devices.torch_gc()
```

**ライブプレビュー**:
```python
def set_current_image():
    """現在の latent から画像を生成してプレビュー更新"""
    if self.sampling_step - self.current_image_sampling_step >= opts.show_progress_every_n_steps:
        self.do_set_current_image()

def do_set_current_image():
    """実際にプレビュー画像を生成"""
    if opts.show_progress_grid:
        self.assign_current_image(modules.sd_samplers.samples_to_image_grid(self.current_latent))
    else:
        self.assign_current_image(modules.sd_samplers.sample_to_image(self.current_latent))
```

**グローバルインスタンス**:
```python
state = State()
state.server_start = time.time()
```

### 4. `opts` - アプリケーション設定（Options クラス）

`/mnt/d/stable-diffusion-webui/modules/shared.py:555-707`

#### Options クラスの設計

**動的プロパティアクセス**:
```python
class Options:
    data = None  # 実際の設定値を保持する辞書
    data_labels = options_templates  # 設定の定義とメタデータ

    def __getattr__(self, item):
        """opts.some_setting のように直接アクセス可能"""
        if item in self.data:
            return self.data[item]
        if item in self.data_labels:
            return self.data_labels[item].default

    def __setattr__(self, key, value):
        """設定値の更新時にバリデーション"""
        # セキュリティチェック
        assert not cmd_opts.freeze_settings, "changing settings is disabled"

        # 制限されたオプションのチェック
        if cmd_opts.hide_ui_dir_config and key in restricted_opts:
            raise RuntimeError(f"not possible to set {key} because it is restricted")

        self.data[key] = value
```

**設定変更時のコールバック**:
```python
def set(self, key, value):
    """設定を変更し、onchange コールバックを実行"""
    oldval = self.data.get(key, None)
    if oldval == value:
        return False  # 変更なし

    setattr(self, key, value)

    if self.data_labels[key].onchange is not None:
        try:
            self.data_labels[key].onchange()  # コールバック実行
        except Exception as e:
            errors.display(e, f"changing setting {key} to {value}")
            setattr(self, key, oldval)  # ロールバック
            return False

    return True
```

**設定の保存・読み込み**:
```python
def save(self, filename):
    """config.json に保存"""
    with open(filename, "w", encoding="utf8") as file:
        json.dump(self.data, file, indent=4)

def load(self, filename):
    """config.json から読み込み"""
    with open(filename, "r", encoding="utf8") as file:
        self.data = json.load(file)

    # バージョン間の設定マイグレーション
    # 型チェックとバリデーション
```

**onchange コールバック登録**:
```python
def onchange(self, key, func, call=True):
    """設定変更時のコールバックを登録"""
    item = self.data_labels.get(key)
    item.onchange = func
    if call:
        func()  # 即座に実行
```

#### OptionInfo - 設定のメタデータ

`/mnt/d/stable-diffusion-webui/modules/shared.py:235-270`

```python
class OptionInfo:
    def __init__(self, default=None, label="", component=None,
                 component_args=None, onchange=None, section=None,
                 refresh=None, comment_before='', comment_after=''):
        self.default = default               # デフォルト値
        self.label = label                   # UI表示ラベル
        self.component = component           # Gradioコンポーネント（Slider, Dropdown等）
        self.component_args = component_args # コンポーネント引数
        self.onchange = onchange             # 変更時コールバック
        self.section = section               # 設定セクション
        self.refresh = refresh               # リフレッシュ関数
        self.comment_before = comment_before # 前置コメント（HTML）
        self.comment_after = comment_after   # 後置コメント（HTML）

    def link(self, label, url):
        """設定にリンクを追加"""
        self.comment_before += f"[<a href='{url}' target='_blank'>{label}</a>]"
        return self

    def info(self, info):
        """設定に情報を追加"""
        self.comment_after += f"<span class='info'>({info})</span>"
        return self

    def needs_restart(self):
        """再起動が必要なことを示す"""
        self.comment_after += " <span class='info'>(requires restart)</span>"
        return self
```

#### 主要な設定カテゴリ

**1. 画像保存設定** (`saving-images`):
- `samples_save`: 画像を常に保存
- `samples_format`: 画像フォーマット（png, jpg, webp）
- `samples_filename_pattern`: ファイル名パターン
- `enable_pnginfo`: PNG に生成パラメータを埋め込む
- `jpeg_quality`: JPEG品質

**2. 保存パス設定** (`saving-paths`):
- `outdir_txt2img_samples`: txt2img 画像の出力先
- `outdir_img2img_samples`: img2img 画像の出力先
- `outdir_extras_samples`: extras 画像の出力先

**3. アップスケール設定** (`upscaling`):
- `ESRGAN_tile`: タイルサイズ
- `realesrgan_enabled_models`: 有効なモデル
- `upscaler_for_img2img`: img2img用アップスケーラー

**4. 顔修復設定** (`face-restoration`):
- `face_restoration_model`: 使用するモデル（CodeFormer/GFPGAN）
- `code_former_weight`: CodeFormer の強度

**5. Stable Diffusion設定** (`sd`):
- `sd_model_checkpoint`: 使用するチェックポイント
- `sd_checkpoint_cache`: RAMにキャッシュするチェックポイント数
- `sd_vae`: 使用するVAE
- `inpainting_mask_weight`: インペイントマスク強度
- `CLIP_stop_at_last_layers`: CLIPスキップ
- `randn_source`: 乱数生成元（GPU/CPU）

**6. 最適化設定** (`optimizations`):
- `cross_attention_optimization`: クロスアテンション最適化
- `token_merging_ratio`: トークンマージング比率
- `s_min_uncond`: ネガティブガイダンス最小シグマ

**7. サンプラーパラメータ** (`sampler-params`):
- `hide_samplers`: 非表示にするサンプラー
- `eta_ddim`: DDIMのeta値
- `eta_ancestral`: Ancestralサンプラーのeta値
- `s_churn`, `s_tmin`, `s_noise`: k-diffusionパラメータ

**8. UI設定** (`ui`):
- `localization`: 言語設定
- `gradio_theme`: Gradioテーマ
- `quicksettings_list`: クイック設定リスト
- `ui_tab_order`: タブの順序
- `hidden_tabs`: 非表示のタブ

**9. ライブプレビュー設定** (`Live previews`):
- `live_previews_enable`: ライブプレビュー有効化
- `show_progress_every_n_steps`: N ステップごとにプレビュー表示
- `show_progress_type`: プレビュー方式（Full/Approx/TAESD）

**グローバルインスタンス**:
```python
opts = Options()
if os.path.exists(config_filename):
    opts.load(config_filename)  # config.json から読み込み
```

### 5. `sd_model` - モデル参照（遅延読み込み）

`/mnt/d/stable-diffusion-webui/modules/shared.py:714-736`

**特殊な実装**: `sys.modules` ハックを使用

```python
class Shared(sys.modules[__name__].__class__):
    """
    sd_model をプロパティとして提供し、オンデマンドで作成・読み込み
    """

    @property
    def sd_model(self):
        import modules.sd_models
        return modules.sd_models.model_data.get_sd_model()

    @sd_model.setter
    def sd_model(self, value):
        import modules.sd_models
        modules.sd_models.model_data.set_sd_model(value)

# モジュールクラスを置き換え
sys.modules[__name__].__class__ = Shared
```

**利点**:
- `import shared; shared.sd_model` でアクセス可能
- 初回アクセス時にモデルを読み込み（遅延読み込み）
- 起動時間の短縮

### 6. その他の重要なグローバル変数

```python
# スタイル管理
prompt_styles = modules.styles.StyleDatabase(styles_filename)

# CLIP Interrogator
interrogator = modules.interrogate.InterrogateModels("interrogate")

# 顔修復モデルリスト
face_restorers = []

# アップスケーラーリスト
sd_upscalers = []

# CLIPモデル
clip_model = None

# Hypernetworks
hypernetworks = {}
loaded_hypernetworks = []

# Gradioテーマ
gradio_theme = gr.themes.Base()

# プログレスバー
total_tqdm = TotalTQDM()

# メモリモニター
mem_mon = modules.memmon.MemUsageMonitor("MemMon", device, opts)
mem_mon.start()
```

### 7. デバイス管理

```python
# コマンドラインオプションに基づいてデバイスを設定
devices.device, devices.device_interrogate, devices.device_gfpgan, \
devices.device_esrgan, devices.device_codeformer = \
    (devices.cpu if any(y in cmd_opts.use_cpu for y in [x, 'all'])
     else devices.get_optimal_device()
     for x in ['sd', 'interrogate', 'gfpgan', 'esrgan', 'codeformer'])

# データ型設定
devices.dtype = torch.float32 if cmd_opts.no_half else torch.float16
devices.dtype_vae = torch.float32 if cmd_opts.no_half or cmd_opts.no_half_vae else torch.float16

# ローカル参照
device = devices.device
```

**重要な変数**:
```python
batch_cond_uncond = cmd_opts.always_batch_cond_uncond or \
                    not (cmd_opts.lowvram or cmd_opts.medvram)

parallel_processing_allowed = not cmd_opts.lowvram and not cmd_opts.medvram

xformers_available = False  # 後で xformers インポート時に更新

weight_load_location = None if cmd_opts.lowram else "cpu"
```

## 設定変更時のコールバック例

`webui.py:configure_opts_onchange()` で登録：

```python
# モデル変更時
shared.opts.onchange("sd_model_checkpoint",
    wrap_queued_call(lambda: modules.sd_models.reload_model_weights()),
    call=False)

# VAE変更時
shared.opts.onchange("sd_vae",
    wrap_queued_call(lambda: modules.sd_vae.reload_vae_weights()),
    call=False)

# 最適化方式変更時
shared.opts.onchange("cross_attention_optimization",
    wrap_queued_call(lambda: modules.sd_hijack.model_hijack.redo_hijack(shared.sd_model)),
    call=False)
```

## ユーティリティ関数

```python
def listfiles(dirname):
    """ディレクトリ内のファイル一覧（隠しファイル除外）"""
    filenames = [os.path.join(dirname, x) for x in sorted(os.listdir(dirname), key=str.lower)
                 if not x.startswith(".")]
    return [file for file in filenames if os.path.isfile(file)]

def walk_files(path, allowed_extensions=None):
    """再帰的にファイルを探索（隠しディレクトリ除外可能）"""
    for root, _, files in os.walk(path, followlinks=True):
        for filename in files:
            if allowed_extensions is not None:
                _, ext = os.path.splitext(filename)
                if ext not in allowed_extensions:
                    continue

            if not opts.list_hidden_files and ("/." in root or "\\." in root):
                continue

            yield os.path.join(root, filename)

def html(filename):
    """html/ ディレクトリからHTMLファイルを読み込み"""
    path = html_path(filename)
    if os.path.exists(path):
        with open(path, encoding="utf8") as file:
            return file.read()
    return ""
```

## TotalTQDM - 全体進捗バー

`/mnt/d/stable-diffusion-webui/modules/shared.py:781-814`

```python
class TotalTQDM:
    """複数のジョブにまたがる全体進捗を表示"""

    def reset(self):
        self._tqdm = tqdm.tqdm(
            desc="Total progress",
            total=state.job_count * state.sampling_steps,
            position=1,
            file=progress_print_out
        )

    def update(self):
        """1ステップ進める"""
        if not opts.multiple_tqdm:
            return
        if self._tqdm is None:
            self.reset()
        self._tqdm.update()

    def updateTotal(self, new_total):
        """総ステップ数を更新"""
        self._tqdm.total = new_total
```

## 設計の特徴と利点

### 1. 中央集権的な状態管理
- すべてのモジュールが `import shared` で状態にアクセス
- グローバル変数を一箇所に集約
- 状態の可視性が高い

### 2. 動的設定システム
- `OptionInfo` でメタデータを定義
- UI自動生成（`ui_settings.py`）
- onchange コールバックで動的な設定変更

### 3. 遅延読み込み
- `sd_model` プロパティで必要時にモデルを読み込み
- 起動時間の短縮
- メモリ効率の向上

### 4. スレッドセーフな処理制御
- `State` クラスで処理状態を管理
- `threading.Event` でサーバーコマンド待機
- `skip()`, `interrupt()` で安全に処理を中断

### 5. セキュリティ対策
- `restricted_opts` で一部設定を制限
- `freeze_settings` で設定変更を無効化
- `hide_ui_dir_config` でディレクトリ設定を隠す

## 他のモジュールとの連携

### webui.py
- `shared.demo` に Gradio アプリを格納
- `shared.state` で処理状態を監視
- `shared.opts` で設定を参照

### processing.py
- `shared.state` で進捗を更新
- `shared.opts` で生成パラメータを参照
- `shared.sd_model` でモデルを使用

### ui.py
- `shared.opts` から UI を自動生成
- `shared.state` で進捗表示
- `shared.demo` に UI を登録

### sd_models.py
- `shared.sd_model` プロパティから呼ばれる
- `shared.opts.sd_model_checkpoint` でモデル選択

## まとめ

`shared.py` は以下を提供：

1. **グローバル状態管理** (`state`)
2. **設定管理** (`opts`, `Options`, `OptionInfo`)
3. **モデル参照** (`sd_model` プロパティ）
4. **コマンドライン引数** (`cmd_opts`)
5. **デバイス管理** (`devices`)
6. **ユーティリティ関数**

このファイルはアプリケーション全体の「神経中枢」として機能し、すべてのモジュールから参照される最重要ファイルの一つです。
