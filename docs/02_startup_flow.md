# Stable Diffusion WebUI - 起動フロー詳細解析

## 起動シーケンス全体図

```
launch.py (エントリーポイント)
    ↓
launch_utils.prepare_environment() → 環境準備
    ↓
launch_utils.start()
    ↓
webui.py の webui() または api_only()
    ↓
initialize() → すべての初期化
    ↓
modules.ui.create_ui() → UI構築
    ↓
Gradio起動 → サーバー開始
    ↓
無限ループで待機（再起動可能）
```

## 1. launch.py - シンプルなエントリーポイント

`/mnt/d/stable-diffusion-webui/launch.py:27-38`

```python
def main():
    if not args.skip_prepare_environment:
        prepare_environment()  # 環境準備

    if args.test_server:
        configure_for_tests()  # テストモード設定

    start()  # WebUI起動
```

**役割**:
- 環境準備とWebUI起動の橋渡し
- 実際の処理は `modules.launch_utils` に全て委譲

## 2. launch_utils.py - 環境準備とインストール

`/mnt/d/stable-diffusion-webui/modules/launch_utils.py`

### 2.1 prepare_environment() - 最重要関数

この関数が起動時の環境構築を全て担当：

#### Pythonバージョンチェック
```python
def check_python_version():
    # Windows: Python 3.10のみ
    # Linux/Mac: Python 3.7-3.11サポート
```

#### PyTorchインストール
```python
torch_command = "pip install torch==2.0.1 torchvision==0.15.2 --extra-index-url {torch_index_url}"
# デフォルト: CUDA 11.8版PyTorch
```

#### 外部リポジトリのクローン
```python
# 以下のGitリポジトリを repositories/ にクローン:
git_clone(stable_diffusion_repo, "Stable Diffusion")  # Stability-AIの公式実装
git_clone(k_diffusion_repo, "K-diffusion")            # Katherine Crowson のサンプラー
git_clone(codeformer_repo, "CodeFormer")              # 顔修正AI
git_clone(blip_repo, "BLIP")                          # 画像キャプション生成
```

#### 依存パッケージインストール
1. **gfpgan** - 顔修正（GAN）
2. **clip** - OpenAI CLIP
3. **open_clip** - オープンソースCLIP
4. **xformers** (オプション) - メモリ最適化
5. **requirements_versions.txt** - その他の依存関係

#### 拡張機能のインストーラー実行
```python
run_extensions_installers(settings_file)
# 各拡張機能の install.py を実行
```

### 2.2 start() - webui.pyへの移行

`/mnt/d/stable-diffusion-webui/modules/launch_utils.py:338-344`

```python
def start():
    print(f"Launching {'API server' if '--nowebui' in sys.argv else 'Web UI'}")
    import webui
    if '--nowebui' in sys.argv:
        webui.api_only()  # APIのみモード
    else:
        webui.webui()     # 通常のWebUIモード
```

## 3. webui.py - メインアプリケーション

`/mnt/d/stable-diffusion-webui/webui.py`

### 3.1 初期import（起動時間測定付き）

```python
startup_timer = timer.startup_timer

import torch
startup_timer.record("import torch")

import gradio
startup_timer.record("import gradio")

import ldm.modules.encoders.modules  # Latent Diffusion Model
startup_timer.record("import ldm")

# その他重要なモジュールのimport
from modules import shared, sd_samplers, upscaler, extensions, ...
```

**ポイント**: 各importの時間を計測して起動時間を最適化

### 3.2 initialize() - 初期化メイン関数

`/mnt/d/stable-diffusion-webui/webui.py:236-253`

```python
def initialize():
    fix_asyncio_event_loop_policy()      # asyncioイベントループ修正
    validate_tls_options()                # TLS設定検証
    configure_sigint_handler()            # Ctrl+Cハンドラ設定
    check_versions()                      # PyTorch/xformersバージョンチェック
    modelloader.cleanup_models()          # 古いモデルクリーンアップ
    configure_opts_onchange()             # 設定変更時のコールバック登録

    modules.sd_models.setup_model()       # ★ SDモデルのセットアップ（重要）
    codeformer.setup_model()              # CodeFormer準備
    gfpgan.setup_model()                  # GFPGAN準備

    initialize_rest(reload_script_modules=False)
```

#### configure_opts_onchange() - 設定変更の監視

`/mnt/d/stable-diffusion-webui/webui.py:226-233`

```python
def configure_opts_onchange():
    # モデル変更時 → モデルを再読み込み
    shared.opts.onchange("sd_model_checkpoint",
                         wrap_queued_call(lambda: modules.sd_models.reload_model_weights()))

    # VAE変更時 → VAEを再読み込み
    shared.opts.onchange("sd_vae",
                         wrap_queued_call(lambda: modules.sd_vae.reload_vae_weights()))

    # 最適化方式変更時 → モデルのhijackをやり直し
    shared.opts.onchange("cross_attention_optimization",
                         wrap_queued_call(lambda: modules.sd_hijack.model_hijack.redo_hijack(shared.sd_model)))
```

### 3.3 initialize_rest() - 残りの初期化

`/mnt/d/stable-diffusion-webui/webui.py:256-324`

```python
def initialize_rest(*, reload_script_modules=False):
    sd_samplers.set_samplers()              # サンプラー一覧作成
    extensions.list_extensions()             # 拡張機能一覧作成
    restore_config_state_file()              # 設定復元（あれば）

    modules.sd_models.list_models()          # 利用可能なモデル一覧
    localization.list_localizations()        # 翻訳ファイル一覧

    modules.scripts.load_scripts()           # ★ スクリプト読み込み（重要）

    modelloader.load_upscalers()             # アップスケーラー読み込み
    modules.sd_vae.refresh_vae_list()        # VAE一覧更新
    modules.textual_inversion.textual_inversion.list_textual_inversion_templates()

    modules.sd_hijack.list_optimizers()      # 最適化手法一覧
    modules.sd_unet.list_unets()             # UNet一覧

    # ★ 別スレッドでモデル読み込み（非同期）
    Thread(target=load_model).start()

    # ★ 別スレッドでGPU初期化（非同期）
    Thread(target=devices.first_time_calculation).start()

    shared.reload_hypernetworks()            # Hypernetwork読み込み
    ui_extra_networks.initialize()           # Extra Networks UI初期化
    extra_networks.initialize()              # Extra Networks初期化
```

**重要な設計**: モデル読み込みとGPU初期化を別スレッドで実行することで、UIの起動を待たせない

### 3.4 webui() - メインループ

`/mnt/d/stable-diffusion-webui/webui.py:371-471`

```python
def webui():
    launch_api = cmd_opts.api
    initialize()  # 初期化実行

    while 1:  # ★ 無限ループ（再起動可能にするため）
        # 一時ディレクトリクリーンアップ
        if shared.opts.clean_temp_dir_at_start:
            ui_tempdir.cleanup_tmpdr()

        # コールバック実行
        modules.script_callbacks.before_ui_callback()

        # ★ UI構築（最重要）
        shared.demo = modules.ui.create_ui()

        # Gradioキュー設定
        if not cmd_opts.no_gradio_queue:
            shared.demo.queue(64)

        # 認証設定
        gradio_auth_creds = list(get_gradio_auth_creds()) or None

        # ★ Gradio起動
        app, local_url, share_url = shared.demo.launch(
            share=cmd_opts.share,
            server_name=server_name,
            server_port=cmd_opts.port,
            ssl_keyfile=cmd_opts.tls_keyfile,
            ssl_certfile=cmd_opts.tls_certfile,
            auth=gradio_auth_creds,
            inbrowser=cmd_opts.autolaunch,
            prevent_thread_lock=True,
        )

        # CORS設定（セキュリティ対策）
        app.user_middleware = [x for x in app.user_middleware
                               if x.cls.__name__ != 'CORSMiddleware']
        setup_middleware(app)

        # API追加
        modules.progress.setup_progress_api(app)
        modules.ui.setup_ui_api(app)
        if launch_api:
            create_api(app)

        # Extra Networks追加
        ui_extra_networks.add_pages_to_demo(app)

        # コールバック実行
        modules.script_callbacks.app_started_callback(shared.demo, app)

        print(f"Startup time: {startup_timer.summary()}.")

        # ★ サーバーコマンド待機ループ
        try:
            while True:
                server_command = shared.state.wait_for_server_command(timeout=5)
                if server_command:
                    if server_command in ("stop", "restart"):
                        break
        except KeyboardInterrupt:
            server_command = "stop"

        if server_command == "stop":
            shared.demo.close()
            break  # 完全停止

        # ★ 再起動処理
        print('Restarting UI...')
        shared.demo.close()
        time.sleep(0.5)
        startup_timer.reset()
        modules.script_callbacks.app_reload_callback()
        modules.script_callbacks.script_unloaded_callback()
        initialize_rest(reload_script_modules=True)  # 再初期化
```

**重要な設計ポイント**:
1. **無限ループ**: UIを停止せずに再起動可能
2. **prevent_thread_lock=True**: Gradioがメインスレッドをブロックしない
3. **再起動時は initialize_rest() のみ**: 完全な再初期化は不要

### 3.5 api_only() - APIのみモード

`/mnt/d/stable-diffusion-webui/webui.py:353-363`

```python
def api_only():
    initialize()

    app = FastAPI()
    setup_middleware(app)
    api = create_api(app)

    modules.script_callbacks.app_started_callback(None, app)

    api.launch(server_name="0.0.0.0" if cmd_opts.listen else "127.0.0.1",
               port=cmd_opts.port if cmd_opts.port else 7861)
```

**用途**: WebUIなしでAPIのみを提供（軽量モード）

## 4. 起動フローまとめ

### フェーズ1: 環境準備（launch_utils.prepare_environment）
1. Pythonバージョンチェック
2. PyTorchインストール/検証
3. 外部リポジトリクローン（Stable Diffusion, k-diffusion等）
4. 依存パッケージインストール（gfpgan, clip等）
5. 拡張機能のインストーラー実行

### フェーズ2: 初期化（webui.initialize）
1. asyncio/TLS/シグナルハンドラ設定
2. バージョンチェック
3. **モデルセットアップ** ← 最重要
4. CodeFormer/GFPGAN準備
5. 設定変更コールバック登録

### フェーズ3: リソース読み込み（webui.initialize_rest）
1. サンプラー/拡張機能/モデル一覧作成
2. **スクリプト読み込み** ← カスタム機能
3. アップスケーラー/VAE/Textual Inversion読み込み
4. **モデル読み込み（別スレッド）** ← 非同期で実行
5. GPU初期化（別スレッド）
6. Hypernetwork/Extra Networks初期化

### フェーズ4: UI起動（webui.webui）
1. before_ui_callbackコールバック実行
2. **UI構築（modules.ui.create_ui）** ← 次の重要ステップ
3. Gradio起動
4. CORS/ミドルウェア設定
5. API追加
6. app_started_callbackコールバック実行
7. サーバーコマンド待機ループ

## 5. 重要な設計原則

### 5.1 段階的な読み込み
- UIを先に表示してユーザーが待たされない
- モデルやGPU初期化は別スレッドで非同期実行
- 必要なものを必要なタイミングで読み込む

### 5.2 再起動可能な設計
- 無限ループで再起動を待機
- 設定変更時に完全な再起動なしで反映可能
- `initialize_rest()` で部分的な再初期化

### 5.3 拡張可能性
- スクリプトシステム（scripts/）
- 拡張機能システム（extensions/）
- コールバックシステム（script_callbacks）
- 各フェーズでカスタムコード実行可能

### 5.4 エラーハンドリング
- バージョンチェック
- CUDA利用可能性チェック
- 依存パッケージの自動インストール
- エラー時の詳細メッセージ表示

### 5.5 パフォーマンス最適化
- startup_timerで各フェーズの時間を測定
- 非同期読み込み
- xformersオプション（メモリ効率化）
- lowvramモード（4GB GPU対応）

## 6. コマンドライン引数（重要なもの）

起動時に指定できる主要な引数：

- `--skip-prepare-environment`: 環境準備をスキップ
- `--skip-python-version-check`: Pythonバージョンチェックスキップ
- `--skip-torch-cuda-test`: CUDA利用可能性チェックスキップ
- `--skip-version-check`: PyTorch/xformersバージョンチェックスキップ
- `--reinstall-torch`: PyTorchを再インストール
- `--reinstall-xformers`: xformersを再インストール
- `--xformers`: xformersを使用（メモリ最適化）
- `--api`: REST APIを有効化
- `--nowebui`: WebUIなし、APIのみモード
- `--share`: Gradio共有リンク作成
- `--listen`: 0.0.0.0でリッスン（外部アクセス許可）
- `--port`: ポート番号指定（デフォルト: 7860）
- `--gradio-auth`: Basic認証設定
- `--autolaunch`: 起動時にブラウザを自動起動
- `--ui-debug-mode`: UI高速デバッグモード

## 次のステップ

- [ ] shared.pyのグローバル状態管理の詳細解析
- [ ] modules.ui.create_ui()のUI構築ロジック解析
- [ ] modules.sd_models.setup_model()のモデル読み込み解析
- [ ] modules.scripts.load_scripts()のスクリプトシステム解析
- [ ] processing.pyの画像生成パイプライン解析
