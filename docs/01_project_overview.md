# Stable Diffusion WebUI - プロジェクト概要

## 基本情報

**プロジェクト名**: Stable Diffusion web UI (AUTOMATIC1111版)
**主な技術**: Python, Gradio, PyTorch
**目的**: Stable Diffusion用のブラウザベースのGUIインターフェース

## プロジェクト構造

### ルートレベルのファイル

#### エントリーポイント
- `launch.py` - メイン起動スクリプト（シンプルなラッパー）
- `webui.py` - Web UIのメイン実行ファイル
- `webui-user.bat` / `webui.bat` - Windows用起動スクリプト
- `webui.sh` / `webui-user.sh` - Linux/Mac用起動スクリプト

#### 設定ファイル
- `config.json` - メイン設定ファイル
- `ui-config.json` - UIの状態と設定
- `params.txt` - パラメータ保存
- `styles.csv` - プロンプトスタイルのデータベース

#### 依存関係
- `requirements.txt` - Python依存パッケージ
- `requirements_versions.txt` - バージョン固定の依存関係
- `package.json` / `package-lock.json` - Node.js依存関係（フロントエンド用）

### 主要ディレクトリ

#### `/modules/` - コアモジュール（最重要）
プロジェクトの全機能を担うPythonモジュール群：

**初期化・起動関連**:
- `launch_utils.py` - 起動ユーティリティ、環境準備
- `initialize.py` / `initialize_util.py` - 初期化処理
- `cmd_args.py` - コマンドライン引数処理
- `paths.py` / `paths_internal.py` - パス管理

**UI関連**:
- `ui.py` (89KB) - メインUIロジック（最大のファイル）
- `ui_common.py` - 共通UI機能
- `ui_components.py` - カスタムUIコンポーネント
- `ui_extensions.py` - 拡張機能UI
- `ui_extra_networks.py` - 追加ネットワーク（embeddings等）UI
- `ui_settings.py` - 設定画面
- `ui_loadsave.py` - 設定の保存/読み込み
- `ui_checkpoint_merger.py` - モデル統合UI
- `ui_postprocessing.py` - 後処理UI
- `ui_prompt_styles.py` - プロンプトスタイルUI
- `ui_tempdir.py` - 一時ディレクトリ管理
- `ui_gradio_extensions.py` - Gradio拡張

**モデル管理**:
- `sd_models.py` (21KB) - Stable Diffusionモデル管理の中核
- `sd_models_config.py` - モデル設定
- `sd_models_types.py` - モデルタイプ定義
- `sd_models_xl.py` - SDXL（Stable Diffusion XL）サポート
- `modelloader.py` - 汎用モデルローダー
- `sd_vae.py` - VAE（Variational Autoencoder）管理
- `sd_vae_approx.py` - VAE近似版
- `sd_vae_taesd.py` - TAESD VAE

**サンプリング・生成**:
- `sd_samplers.py` - サンプラー管理
- `sd_samplers_common.py` - サンプラー共通機能
- `sd_samplers_compvis.py` - CompVisサンプラー実装
- `sd_samplers_kdiffusion.py` (21KB) - k-diffusionサンプラー
- `sd_samplers_cfg_denoiser.py` - CFG denoiser
- `sd_samplers_timesteps.py` - タイムステップベースサンプラー
- `sd_samplers_timesteps_impl.py` - タイムステップ実装
- `sd_samplers_extra.py` - 追加サンプラー
- `processing.py` (63KB) - 画像生成処理の中核
- `txt2img.py` - テキストから画像生成
- `img2img.py` - 画像から画像生成
- `sd_hijack.py` (41KB) - Stable Diffusion改変/フック
- `sd_hijack_clip.py` - CLIPモデル改変
- `sd_hijack_optimizations.py` (14KB) - 最適化実装
- `sd_hijack_unet.py` - UNet改変
- `sd_unet.py` - UNet管理

**プロンプト処理**:
- `prompt_parser.py` (40KB) - プロンプト解析（重要）
- `styles.py` - スタイル管理
- `interrogate.py` - CLIP interrogator（画像からプロンプト生成）

**画像処理**:
- `images.py` (29KB) - 画像保存、メタデータ管理
- `masking.py` - マスク処理
- `extras.py` - 追加機能（upscale等）
- `postprocessing.py` - 後処理
- `upscaler.py` - アップスケーラー基底クラス
- `realesrgan_model.py` - RealESRGANアップスケーラー
- `esrgan_model.py` / `esrgan_model_arch.py` - ESRGANアップスケーラー
- `gfpgan_model.py` - GFPGAN（顔修正）
- `codeformer_model.py` - CodeFormer（顔修正）

**ニューラルネットワーク拡張**:
- `extra_networks.py` - 追加ネットワーク基底クラス
- `extra_networks_hypernet.py` - Hypernetwork
- `/hypernetworks/` - Hypernetwork実装
- `/textual_inversion/` - Textual Inversion実装

**設定・共有状態**:
- `shared.py` (47KB) - グローバル状態管理（超重要）
- `shared_cmd_options.py` - 共有コマンドオプション
- `shared_gradio_themes.py` - Gradioテーマ
- `shared_init.py` - 共有初期化
- `shared_items.py` - 共有アイテム
- `shared_options.py` (37KB) - 共有オプション定義
- `shared_state.py` - 共有状態
- `shared_total_tqdm.py` - プログレスバー
- `options.py` - オプション管理

**拡張機能**:
- `extensions.py` - 拡張機能システム
- `scripts.py` (45KB) - スクリプトシステム
- `script_callbacks.py` - コールバックシステム

**デバイス・最適化**:
- `devices.py` - GPU/CPU管理
- `lowvram.py` - VRAM節約モード
- `mac_specific.py` - Mac固有の最適化
- `sub_quadratic_attention.py` - メモリ効率的なAttention実装

**ユーティリティ**:
- `cache.py` - キャッシュ管理
- `hashes.py` - ハッシュ計算
- `errors.py` - エラーハンドリング
- `timer.py` - タイマー
- `memmon.py` - メモリモニタリング
- `sysinfo.py` - システム情報
- `localization.py` - 多言語対応
- `generation_parameters_copypaste.py` (16KB) - パラメータコピペ機能
- `call_queue.py` - 呼び出しキュー
- `util.py` - 汎用ユーティリティ

**API**:
- `/api/` - REST API実装

**モデル関連サブディレクトリ**:
- `/models/` - モデルアーキテクチャ定義
- `/codeformer/` - CodeFormer関連

#### `/models/` - AIモデルの保存場所
実際の学習済みモデルファイルを保存：
- `Stable-diffusion/` - SDモデル（.ckpt, .safetensors）
- `VAE/` - VAEモデル
- `hypernetworks/` - Hypernetworkモデル
- `Lora/` - LoRAモデル
- など

#### `/outputs/` - 生成画像の保存先
- `txt2img-images/`
- `img2img-images/`
- `extras-images/`
- など、用途別にサブフォルダ

#### `/extensions/` - ユーザーインストール拡張機能
コミュニティが開発した拡張機能をインストール

#### `/extensions-builtin/` - ビルトイン拡張機能
公式に含まれる拡張機能

#### `/scripts/` - カスタムスクリプト
ユーザーがUIから実行できるカスタムスクリプト

#### `/embeddings/` - Textual Inversion埋め込み
学習済みembeddingファイル

#### `/configs/` - モデル設定ファイル
各種モデルのYAML設定

#### `/repositories/` - 依存する外部リポジトリ
GitサブモジュールやクローンされたGitリポジトリ

#### `/javascript/` - フロントエンドJavaScript
UI拡張用のJSファイル

#### `/html/` - HTML/CSS
UIのHTML/CSSリソース

#### `/localizations/` - 翻訳ファイル
多言語対応の翻訳JSON

#### `/textual_inversion_templates/` - TI学習用テンプレート

#### `/venv/` - Python仮想環境
依存パッケージがインストールされる場所

## 主要な依存ライブラリ

### コア機能
- **torch** - PyTorchディープラーニングフレームワーク
- **transformers==4.25.1** - HuggingFace Transformers（CLIP等）
- **gradio==3.32.0** - WebUIフレームワーク
- **accelerate** - PyTorch高速化

### 画像処理
- **Pillow** - Python画像処理ライブラリ
- **numpy** - 数値計算
- **scikit-image** - 画像処理アルゴリズム
- **kornia** - 微分可能なコンピュータビジョン
- **einops** - テンソル操作

### Diffusionモデル
- **pytorch_lightning** - PyTorchトレーニングフレームワーク
- **omegaconf** - 設定管理
- **safetensors** - 安全なテンソル保存形式
- **torchdiffeq** / **torchsde** - 微分方程式ソルバー
- **tomesd** - Token Merging for Stable Diffusion

### アップスケール・顔修正
- **gfpgan** - 顔修正AI
- **realesrgan** - 高品質アップスケール
- **basicsr** - 超解像ベースライン

### ユーティリティ
- **requests** - HTTP通信
- **GitPython** - Git操作
- **psutil** - システムユーティリティ
- **timm** - PyTorch画像モデル
- **lark** - パーサージェネレーター（プロンプト解析用）
- **jsonmerge** / **inflection** - データ処理
- **piexif** - EXIF情報処理
- **blendmodes** - ブレンドモード
- **clean-fid** - FIDスコア計算
- **resize-right** - 高品質リサイズ

## launch.py の仕組み

```python
# launch.pyは非常にシンプルな構造
from modules import launch_utils

def main():
    if not args.skip_prepare_environment:
        prepare_environment()  # 環境準備（依存関係チェック、インストール）

    if args.test_server:
        configure_for_tests()  # テストモード設定

    start()  # WebUI起動

if __name__ == "__main__":
    main()
```

実際の処理はすべて `modules/launch_utils.py` に委譲されている。

## 重要な設計ポイント

1. **モジュラー設計**: 機能ごとにモジュールが分離
2. **拡張可能性**: extensions/, scripts/で機能追加可能
3. **グローバル状態管理**: shared.pyで一元管理
4. **Gradioベース**: WebUIはGradioフレームワークを使用
5. **最適化重視**: 複数のメモリ最適化手法を実装

## 次のステップ

- [ ] launch_utils.pyの詳細解析
- [ ] webui.pyの起動フロー解析
- [ ] shared.pyのグローバル状態管理の理解
- [ ] processing.pyの画像生成パイプライン解析
- [ ] ui.pyのUI構築ロジック解析
