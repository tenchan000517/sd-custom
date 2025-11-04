"""
Simple Editor - かんたん画像編集

シンプルで直感的なUI：
1. スタイル変換モード: 実写 → イラスト風などに変換
2. 部分編集モード: ブラシで選択 → 文章で指示
"""

import gradio as gr
from modules.processing import StableDiffusionProcessingImg2Img, process_images
from modules.shared import opts, state
import modules.shared as shared
import modules.script_callbacks as script_callbacks


def create_unified_tab():
    """統合UI作成"""

    # スタイルプリセット
    STYLES = {
        "写真そのまま": {
            "prompt": "",
            "negative": ""
        },
        "高品質アニメ（推奨）": {
            "prompt": "masterpiece, best quality, high quality, extremely detailed, anime style, cel shading, clean lineart, detailed face, beautiful detailed eyes, glossy hair, shiny hair, soft lighting, professional illustration, vibrant colors",
            "negative": "lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry, artist name, photo, photorealistic, realistic, 3d render, sketch, unfinished"
        },
        "アニメ風": {
            "prompt": "anime style, high quality, detailed, vibrant colors, illustration",
            "negative": "photo, photorealistic, realistic, 3d render"
        },
        "水彩画風": {
            "prompt": "watercolor painting, soft colors, artistic, traditional art",
            "negative": "photo, digital art, 3d, sharp edges"
        },
        "油絵風": {
            "prompt": "oil painting, canvas texture, brush strokes, classical art, fine art",
            "negative": "photo, anime, digital, flat"
        },
        "漫画風": {
            "prompt": "manga style, black and white, screentone, ink drawing, comic",
            "negative": "photo, color, realistic, 3d"
        },
        "3Dレンダリング風": {
            "prompt": "3d render, octane render, highly detailed, professional, cg",
            "negative": "photo, 2d, flat, hand drawn"
        },
        "ジブリ風": {
            "prompt": "studio ghibli style, anime, hand drawn, miyazaki, soft colors, beautiful background",
            "negative": "photo, 3d, cg, dark, modern"
        },
        "ピクサー風": {
            "prompt": "pixar style, 3d animation, disney, colorful, cute, professional render",
            "negative": "photo, 2d, anime, realistic, dark"
        },
    }

    def process_image(input_image, mode, style, edit_prompt, strength, steps_count):
        """画像処理メイン関数"""

        if input_image is None:
            return None, "⚠️ 画像をアップロードしてください"

        # モード判定
        is_style_mode = (mode == "スタイル変換")

        # スタイル変換モード
        if is_style_mode:
            style_config = STYLES.get(style, STYLES["アニメ風"])
            prompt = style_config["prompt"]
            negative = style_config["negative"]
            mask = None
            actual_image = input_image

        # 部分編集モード
        else:
            prompt = edit_prompt if edit_prompt else "high quality, detailed"
            negative = "low quality, blurry, deformed, bad anatomy"

            # Gradio sketchツールからマスク取得
            if isinstance(input_image, dict):
                mask = input_image.get("mask")
                actual_image = input_image.get("image")
            else:
                mask = None
                actual_image = input_image

        if actual_image is None:
            return None, "⚠️ 画像が読み込めませんでした"

        # 画像サイズ取得
        try:
            width = actual_image.width
            height = actual_image.height
        except:
            width = 512
            height = 512

        # 処理パラメータ設定
        p = StableDiffusionProcessingImg2Img(
            sd_model=shared.sd_model,
            outpath_samples=opts.outdir_samples or opts.outdir_img2img_samples,
            outpath_grids=opts.outdir_grids or opts.outdir_img2img_grids,
            prompt=prompt,
            negative_prompt=negative,
            init_images=[actual_image],
            mask=mask,
            mask_blur=4 if mask else 0,
            inpainting_fill=1,  # original
            denoising_strength=strength,
            sampler_name="DPM++ 2M Karras",  # 高品質サンプラー
            steps=steps_count,
            cfg_scale=8.0,  # プロンプトへの従順度アップ
            width=width,
            height=height,
            seed=-1,
            batch_size=1,
            n_iter=1,
            resize_mode=0,
            inpaint_full_res=False,
        )

        # 処理実行
        try:
            state.begin()
            processed = process_images(p)
            state.end()
            p.close()

            if processed and len(processed.images) > 0:
                result_image = processed.images[0]

                if is_style_mode:
                    info = f"✅ 変換完了！\nスタイル: {style}\n強さ: {strength}\nステップ: {steps_count}"
                else:
                    info = f"✅ 編集完了！\n指示: {edit_prompt}\n強さ: {strength}\nステップ: {steps_count}"

                return result_image, info
            else:
                return None, "❌ 処理に失敗しました"

        except Exception as e:
            state.end()
            return None, f"❌ エラーが発生しました: {str(e)}"

    # ========== UI構築 ==========
    with gr.Blocks(theme=gr.themes.Soft()) as ui:
        gr.Markdown("# 🎨 かんたん画像編集")
        gr.Markdown("実写をイラストに変換したり、画像の一部を編集したり、簡単にできます！")

        with gr.Row():
            # 左カラム: 入力
            with gr.Column(scale=1):
                # モード選択
                mode = gr.Radio(
                    choices=["スタイル変換", "部分編集"],
                    value="スタイル変換",
                    label="📌 モード選択",
                    info="やりたいことを選んでください"
                )

                # スタイル変換用UI
                with gr.Group(visible=True) as style_group:
                    gr.Markdown("### 📸 スタイル変換")
                    input_image_style = gr.Image(
                        label="画像をアップロード",
                        type="pil",
                        source="upload"
                    )
                    style = gr.Dropdown(
                        choices=list(STYLES.keys()),
                        value="高品質アニメ（推奨）",
                        label="🎨 変換スタイル"
                    )

                # 部分編集用UI
                with gr.Group(visible=False) as edit_group:
                    gr.Markdown("### ✏️ 部分編集")
                    gr.Markdown("**ブラシで編集したい箇所を白く塗ってください**")
                    input_image_edit = gr.Image(
                        label="画像をアップロード（ブラシツールで編集箇所を塗る）",
                        type="pil",
                        source="upload",
                        tool="sketch",
                        brush_radius=20,
                    )
                    edit_prompt = gr.Textbox(
                        label="💬 変更内容を文章で入力",
                        placeholder='例: 「赤い帽子をかぶせて」「背景を海にして」「笑顔にして」',
                        lines=2
                    )

                # 共通パラメータ
                with gr.Accordion("⚙️ 詳細設定", open=False):
                    strength = gr.Slider(
                        minimum=0.1,
                        maximum=1.0,
                        value=0.70,
                        step=0.05,
                        label="変換の強さ",
                        info="小さい値 = 元画像に近い、大きい値 = 変換が強い"
                    )
                    steps_count = gr.Slider(
                        minimum=10,
                        maximum=50,
                        value=35,
                        step=5,
                        label="品質（ステップ数）",
                        info="大きいほど高品質だが時間がかかる"
                    )

                # 実行ボタン
                run_btn = gr.Button(
                    "✨ 実行",
                    variant="primary",
                    size="lg"
                )

            # 右カラム: 出力
            with gr.Column(scale=1):
                output = gr.Image(
                    label="🖼️ 結果",
                    type="pil"
                )
                status = gr.Textbox(
                    label="ステータス",
                    lines=4,
                    max_lines=6
                )

        # ========== イベント設定 ==========

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
        def run_with_mode(mode, img_style, img_edit, style, edit_prompt, strength, steps):
            img = img_style if mode == "スタイル変換" else img_edit
            return process_image(img, mode, style, edit_prompt, strength, steps)

        run_btn.click(
            fn=run_with_mode,
            inputs=[
                mode,
                input_image_style,
                input_image_edit,
                style,
                edit_prompt,
                strength,
                steps_count
            ],
            outputs=[output, status]
        )

        # ========== 使い方説明 ==========
        with gr.Accordion("📖 使い方", open=False):
            gr.Markdown("""
            ## スタイル変換モード

            1. **画像をアップロード**: 変換したい画像を選択
            2. **スタイルを選択**: アニメ風、水彩画風など好きなスタイル
            3. **実行ボタンをクリック**: 数秒〜数十秒で完成！

            ### スタイル説明
            - **高品質アニメ（推奨）**: 商業レベルの高品質アニメイラスト。細部まで精密、セルアニメ調
            - **アニメ風**: アニメ・イラスト風に変換（シンプル版）
            - **水彩画風**: 柔らかい水彩画タッチ
            - **油絵風**: 油絵・クラシック絵画風
            - **漫画風**: 漫画・モノクロ風
            - **3Dレンダリング風**: CGっぽい質感
            - **ジブリ風**: スタジオジブリっぽい雰囲気
            - **ピクサー風**: ピクサー/ディズニーアニメ風

            ---

            ## 部分編集モード

            1. **画像をアップロード**
            2. **ブラシで編集したい部分を白く塗る**
               - ブラシサイズは調整可能
               - 塗った部分だけが変更されます
            3. **変更内容を文章で入力**
               - 「赤い帽子をかぶせて」
               - 「背景を夕焼けにして」
               - 「笑顔にして」など
            4. **実行ボタンをクリック**

            ### コツ
            - マスクは少し大きめに塗ると自然な仕上がり
            - 複雑な変更は「強さ」を高めに設定
            - 満足いくまで何度でも試せます！

            ---

            ## 詳細設定

            - **変換の強さ**: 0.6〜0.75 が推奨。小さいほど元画像に近く、大きいほど変換が強い
            - **品質（ステップ数）**: 35がデフォルト（高品質）、より高品質なら40〜50（時間がかかります）

            ### 推奨設定（高品質アニメ）
            - **サンプラー**: DPM++ 2M Karras（自動設定）
            - **変換の強さ**: 0.70
            - **品質**: 35ステップ
            - **モデル**: Counterfeit-V3.0 または animagineXLV3 推奨
            """)

    return [(ui, "かんたん編集", "simple_editor")]


# ========== 登録 ==========
def on_ui_tabs():
    """UIタブ登録"""
    return create_unified_tab()


# コールバック登録
script_callbacks.on_ui_tabs(on_ui_tabs)
