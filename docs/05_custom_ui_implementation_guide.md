# カスタムUI実装ガイド：シンプルな画像変換・編集ツール

## 目標

既存のStable Diffusion WebUIをベースに、以下の機能を持つシンプルなUIを作成：
1. 実写 → イラスト風変換（ワンクリック）
2. 画像の部分編集（直感的なブラシ操作）
3. わかりやすいUI/UX

## 実装戦略

### アプローチ1: 拡張機能として実装（推奨）

**メリット**:
- 既存コードを壊さない
- アップデートの影響を受けにくい
- 独立してメンテナンス可能

**実装場所**: `/extensions/simple-editor/`

### アプローチ2: カスタムタブ追加

**メリット**:
- 既存UIと統合
- 既存の機能を再利用しやすい

**実装場所**: `/scripts/simple_editor.py`

---

## 実装方法1: スタイル変換UI

### ステップ1: 基本スクリプト作成

`/extensions/simple-editor/scripts/style_converter.py`:

```python
import gradio as gr
import modules.scripts as scripts
from modules import sd_samplers
from modules.processing import StableDiffusionProcessingImg2Img, process_images
from modules.shared import opts, state
import modules.shared as shared
from PIL import Image

class StyleConverterScript(scripts.Script):
    def title(self):
        return "Simple Style Converter"

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def ui(self, is_img2img):
        return []

# Gradioタブとして登録
def create_style_converter_tab():
    # スタイルプリセット
    style_presets = {
        "anime": {
            "prompt": "anime style, high quality, detailed, vibrant colors",
            "negative": "photo, photorealistic, realistic, 3d"
        },
        "watercolor": {
            "prompt": "watercolor painting, soft colors, artistic",
            "negative": "photo, digital art, 3d"
        },
        "oil_painting": {
            "prompt": "oil painting, canvas texture, brush strokes, classical art",
            "negative": "photo, anime, digital"
        },
        "manga": {
            "prompt": "manga style, black and white, screentone, ink drawing",
            "negative": "photo, color, realistic"
        },
        "3d": {
            "prompt": "3d render, octane render, highly detailed, professional",
            "negative": "photo, 2d, flat"
        }
    }

    def convert_style(input_image, style_name, strength):
        if input_image is None:
            return None, "画像をアップロードしてください"

        # スタイル設定取得
        style = style_presets.get(style_name, style_presets["anime"])

        # img2img処理
        p = StableDiffusionProcessingImg2Img(
            sd_model=shared.sd_model,
            outpath_samples=opts.outdir_samples or opts.outdir_img2img_samples,
            outpath_grids=opts.outdir_grids or opts.outdir_img2img_grids,
            prompt=style["prompt"],
            negative_prompt=style["negative"],
            init_images=[input_image],
            resize_mode=0,
            denoising_strength=strength,
            seed=-1,
            sampler_name="Euler a",  # 高速サンプラー
            steps=20,  # 少ないステップで高速化
            cfg_scale=7.0,
            width=input_image.width,
            height=input_image.height,
            restore_faces=False,
            tiling=False,
            batch_size=1,
            n_iter=1,
        )

        # 処理実行
        state.begin()
        processed = process_images(p)
        state.end()
        p.close()

        if len(processed.images) > 0:
            result_image = processed.images[0]
            info = f"✅ 変換完了！\nスタイル: {style_name}\n強度: {strength}"
            return result_image, info
        else:
            return None, "❌ 変換に失敗しました"

    # UI構築
    with gr.Blocks() as ui:
        gr.Markdown("# 📸 画像スタイル変換")
        gr.Markdown("実写画像をイラストや絵画風に簡単変換！")

        with gr.Row():
            with gr.Column():
                input_image = gr.Image(label="元の画像", type="pil", source="upload")

                style_choice = gr.Radio(
                    choices=["anime", "watercolor", "oil_painting", "manga", "3d"],
                    value="anime",
                    label="変換スタイル",
                    info="好きなスタイルを選んでください"
                )

                strength_slider = gr.Slider(
                    minimum=0.1,
                    maximum=1.0,
                    value=0.6,
                    step=0.05,
                    label="変換の強さ",
                    info="小さい値 = 元画像に近い、大きい値 = スタイルが強い"
                )

                convert_btn = gr.Button("✨ 変換する", variant="primary", size="lg")

            with gr.Column():
                output_image = gr.Image(label="変換後の画像", type="pil")
                info_text = gr.Textbox(label="ステータス", lines=3)

        # イベント設定
        convert_btn.click(
            fn=convert_style,
            inputs=[input_image, style_choice, strength_slider],
            outputs=[output_image, info_text]
        )

        # 使い方の説明
        gr.Markdown("""
        ## 使い方
        1. **画像をアップロード**: 変換したい画像をドロップまたは選択
        2. **スタイルを選択**: anime（アニメ風）、watercolor（水彩画）など
        3. **強さを調整**: スライダーで変換の強さを調整
        4. **変換ボタンをクリック**: 数秒〜数十秒で完成！

        ### スタイル説明
        - **anime**: アニメ・イラスト風
        - **watercolor**: 柔らかい水彩画風
        - **oil_painting**: 油絵・クラシック絵画風
        - **manga**: 漫画・モノクロ風
        - **3d**: 3Dレンダリング風
        """)

    return [(ui, "スタイル変換", "style_converter")]

# script_callbacks で登録
import modules.script_callbacks as script_callbacks

def on_ui_tabs():
    return create_style_converter_tab()

script_callbacks.on_ui_tabs(on_ui_tabs)
```

### ステップ2: インストールスクリプト

`/extensions/simple-editor/install.py`:

```python
# 必要な依存関係があればここでインストール
print("Simple Editor extension loaded!")
```

---

## 実装方法2: 部分編集UI

### ステップ1: インペイント機能

`/extensions/simple-editor/scripts/smart_editor.py`:

```python
import gradio as gr
import numpy as np
from PIL import Image, ImageDraw
import modules.scripts as scripts
from modules.processing import StableDiffusionProcessingImg2Img, process_images
from modules.shared import opts, state
import modules.shared as shared

def create_smart_editor_tab():
    def edit_image(input_image, mask_image, edit_prompt, strength):
        if input_image is None:
            return None, "画像をアップロードしてください"

        if mask_image is None:
            return None, "編集箇所をマスクしてください"

        # inpainting処理
        p = StableDiffusionProcessingImg2Img(
            sd_model=shared.sd_model,
            outpath_samples=opts.outdir_samples or opts.outdir_img2img_samples,
            outpath_grids=opts.outdir_grids or opts.outdir_img2img_grids,
            prompt=edit_prompt,
            negative_prompt="low quality, blurry, deformed",
            init_images=[input_image],
            mask=mask_image,
            mask_blur=4,
            inpainting_fill=1,  # original
            resize_mode=0,
            denoising_strength=strength,
            seed=-1,
            sampler_name="Euler a",
            steps=20,
            cfg_scale=7.0,
            width=input_image.width,
            height=input_image.height,
            inpaint_full_res=False,
            batch_size=1,
            n_iter=1,
        )

        # 処理実行
        state.begin()
        processed = process_images(p)
        state.end()
        p.close()

        if len(processed.images) > 0:
            result = processed.images[0]
            info = f"✅ 編集完了！\n指示: {edit_prompt}"
            return result, info
        else:
            return None, "❌ 編集に失敗しました"

    # UI構築
    with gr.Blocks() as ui:
        gr.Markdown("# ✏️ スマート画像編集")
        gr.Markdown("ブラシで選択して、文章で指示するだけ！")

        with gr.Row():
            with gr.Column():
                # 画像エディタ（マスク付き）
                image_editor = gr.Image(
                    label="画像を編集",
                    type="pil",
                    source="upload",
                    tool="sketch",  # スケッチツール有効
                    brush_radius=20,
                )

                edit_prompt = gr.Textbox(
                    label="変更内容を文章で指定",
                    placeholder='例: "赤い帽子をかぶせて"、"背景を海にして"、"猫に変えて"',
                    lines=2
                )

                strength_slider = gr.Slider(
                    minimum=0.3,
                    maximum=1.0,
                    value=0.75,
                    step=0.05,
                    label="変更の強さ"
                )

                edit_btn = gr.Button("🎨 適用", variant="primary", size="lg")

            with gr.Column():
                output_image = gr.Image(label="編集結果", type="pil")
                info_text = gr.Textbox(label="ステータス", lines=3)

        # マスク処理のヘルパー関数
        def process_sketch(image_dict):
            if image_dict is None:
                return None, None

            # Gradioのsketchツールは{"image": PIL, "mask": PIL}を返す
            if isinstance(image_dict, dict):
                input_img = image_dict.get("image")
                mask_img = image_dict.get("mask")
                return input_img, mask_img
            else:
                return image_dict, None

        # イベント設定
        def edit_with_mask(image_editor_value, edit_prompt, strength):
            input_img, mask_img = process_sketch(image_editor_value)
            return edit_image(input_img, mask_img, edit_prompt, strength)

        edit_btn.click(
            fn=edit_with_mask,
            inputs=[image_editor, edit_prompt, strength_slider],
            outputs=[output_image, info_text]
        )

        # 使い方
        gr.Markdown("""
        ## 使い方
        1. **画像をアップロード**
        2. **ブラシで編集箇所を塗る**（白く塗った部分が変更される）
        3. **変更内容を文章で入力**
           - 「赤い帽子をかぶせて」
           - 「背景を夕焼けにして」
           - 「笑顔にして」など
        4. **適用ボタンをクリック**

        ### コツ
        - マスクは少し大きめに塗ると自然な仕上がりに
        - 複雑な変更は強度を高めに設定
        - 何度でもやり直し可能！
        """)

    return [(ui, "スマート編集", "smart_editor")]

# 登録
import modules.script_callbacks as script_callbacks

def on_ui_tabs():
    return create_smart_editor_tab()

script_callbacks.on_ui_tabs(on_ui_tabs)
```

---

## 実装方法3: 統合版（両方の機能）

### 最もシンプルな統合UI

`/extensions/simple-editor/scripts/unified_editor.py`:

```python
import gradio as gr
from modules.processing import StableDiffusionProcessingImg2Img, process_images
from modules.shared import opts, state
import modules.shared as shared
import modules.script_callbacks as script_callbacks

def create_unified_tab():
    # スタイルプリセット
    STYLES = {
        "写真そのまま": {"prompt": "", "negative": ""},
        "アニメ風": {"prompt": "anime style, vibrant colors", "negative": "photo, realistic"},
        "水彩画風": {"prompt": "watercolor painting", "negative": "photo"},
        "油絵風": {"prompt": "oil painting", "negative": "photo"},
        "漫画風": {"prompt": "manga style", "negative": "photo, color"},
    }

    def process_image(input_image, mode, style, edit_prompt, strength):
        if input_image is None:
            return None, "画像をアップロードしてください"

        # スタイル適用モード
        if mode == "スタイル変換":
            style_config = STYLES.get(style, STYLES["アニメ風"])
            prompt = style_config["prompt"]
            negative = style_config["negative"]
            mask = None

        # 編集モード
        else:
            prompt = edit_prompt if edit_prompt else "high quality"
            negative = "low quality, blurry"
            # マスク処理（Gradio sketchから取得）
            if isinstance(input_image, dict):
                mask = input_image.get("mask")
                input_image = input_image.get("image")
            else:
                mask = None

        # 処理
        p = StableDiffusionProcessingImg2Img(
            sd_model=shared.sd_model,
            outpath_samples=opts.outdir_samples or opts.outdir_img2img_samples,
            outpath_grids=opts.outdir_grids or opts.outdir_img2img_grids,
            prompt=prompt,
            negative_prompt=negative,
            init_images=[input_image],
            mask=mask,
            mask_blur=4 if mask else 0,
            denoising_strength=strength,
            sampler_name="Euler a",
            steps=20,
            cfg_scale=7.0,
            width=input_image.width if hasattr(input_image, 'width') else 512,
            height=input_image.height if hasattr(input_image, 'height') else 512,
            batch_size=1,
            n_iter=1,
        )

        state.begin()
        processed = process_images(p)
        state.end()
        p.close()

        if processed and len(processed.images) > 0:
            return processed.images[0], "✅ 完了！"
        return None, "❌ 失敗"

    # UI
    with gr.Blocks(theme=gr.themes.Soft()) as ui:
        gr.Markdown("# 🎨 かんたん画像編集")

        with gr.Row():
            with gr.Column(scale=1):
                mode = gr.Radio(
                    choices=["スタイル変換", "部分編集"],
                    value="スタイル変換",
                    label="モード選択"
                )

                # スタイル変換用
                with gr.Group(visible=True) as style_group:
                    input_image_style = gr.Image(label="画像をアップロード", type="pil")
                    style = gr.Dropdown(
                        choices=list(STYLES.keys()),
                        value="アニメ風",
                        label="スタイル"
                    )

                # 部分編集用
                with gr.Group(visible=False) as edit_group:
                    input_image_edit = gr.Image(
                        label="画像をアップロード（ブラシで編集箇所を塗る）",
                        type="pil",
                        tool="sketch"
                    )
                    edit_prompt = gr.Textbox(
                        label="変更内容",
                        placeholder="例: 赤い帽子をかぶせて"
                    )

                strength = gr.Slider(0.1, 1.0, 0.6, label="強さ")
                run_btn = gr.Button("✨ 実行", variant="primary")

            with gr.Column(scale=1):
                output = gr.Image(label="結果")
                status = gr.Textbox(label="ステータス")

        # モード切り替え
        def switch_mode(mode):
            if mode == "スタイル変換":
                return gr.update(visible=True), gr.update(visible=False)
            else:
                return gr.update(visible=False), gr.update(visible=True)

        mode.change(
            fn=switch_mode,
            inputs=[mode],
            outputs=[style_group, edit_group]
        )

        # 実行
        def run_with_mode(mode, img_style, img_edit, style, edit_prompt, strength):
            img = img_style if mode == "スタイル変換" else img_edit
            return process_image(img, mode, style, edit_prompt, strength)

        run_btn.click(
            fn=run_with_mode,
            inputs=[mode, input_image_style, input_image_edit, style, edit_prompt, strength],
            outputs=[output, status]
        )

    return [(ui, "かんたん編集", "simple_editor")]

script_callbacks.on_ui_tabs(create_unified_tab)
```

---

## インストール手順

### 1. 拡張機能フォルダ作成

```bash
cd /mnt/d/stable-diffusion-webui/extensions
mkdir simple-editor
cd simple-editor
mkdir scripts
```

### 2. ファイル配置

```
extensions/simple-editor/
  ├── install.py          # 空ファイルでOK
  └── scripts/
      └── unified_editor.py  # 上記のコードをコピー
```

### 3. WebUI再起動

```bash
cd /mnt/d/stable-diffusion-webui
./webui.bat  # または webui.sh
```

### 4. 新しいタブが追加される

ブラウザで `http://localhost:7860` にアクセスすると、
**「かんたん編集」** タブが追加されています！

---

## カスタマイズポイント

### UIデザインの変更

```python
# テーマ変更
with gr.Blocks(theme=gr.themes.Soft()) as ui:
# または
with gr.Blocks(theme=gr.themes.Default()) as ui:
# または
with gr.Blocks(theme=gr.themes.Monochrome()) as ui:
```

### スタイルプリセット追加

```python
STYLES = {
    "写真そのまま": {"prompt": "", "negative": ""},
    "アニメ風": {"prompt": "anime style", "negative": "photo"},
    # 追加
    "ジブリ風": {
        "prompt": "studio ghibli style, anime, hand drawn",
        "negative": "photo, 3d, cg"
    },
    "ピクサー風": {
        "prompt": "pixar style, 3d animation, disney",
        "negative": "photo, 2d, anime"
    },
}
```

### デフォルトパラメータ調整

```python
# より高品質にしたい場合
steps=30,  # 20 → 30
cfg_scale=9.0,  # 7.0 → 9.0

# より高速にしたい場合
steps=15,  # 20 → 15
sampler_name="LCM",  # 超高速サンプラー（別途モデル必要）
```

---

## さらなる改善案

### 1. プリセット保存機能

ユーザーが独自のスタイルプリセットを保存できるように。

### 2. バッチ処理

複数画像を一括変換。

### 3. Before/After比較表示

スライダーで元画像と比較。

### 4. ワンクリックテンプレート

「SNSアイコン用」「印刷用高解像度」など用途別テンプレート。

### 5. スマホ対応

Gradioはレスポンシブだが、さらにモバイル最適化。

---

## まとめ

このガイドに従えば：
✅ シンプルで直感的なUIを作成
✅ 既存機能を活用して高品質な変換
✅ 拡張機能として独立して開発
✅ 簡単にカスタマイズ可能

次のステップ：
1. 上記のコードを `/extensions/simple-editor/` に配置
2. WebUIを再起動
3. 新しいタブで試してみる
4. 好みに合わせてカスタマイズ

わからないことがあれば、このレポートと一緒に質問してください！
