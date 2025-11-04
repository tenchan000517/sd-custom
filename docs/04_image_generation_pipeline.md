# Stable Diffusion WebUI - 画像生成パイプライン解析

## 概要

画像生成パイプラインは主に3つのファイルで構成されます：
- **`processing.py`** (1327行) - コアロジック、画像生成の中枢
- **`txt2img.py`** (71行) - テキストから画像生成のラッパー
- **`img2img.py`** (212行) - 画像から画像生成のラッパー

## アーキテクチャ

```
txt2img.py / img2img.py (UIから呼ばれる)
    ↓
StableDiffusionProcessingTxt2Img / StableDiffusionProcessingImg2Img 生成
    ↓
process_images(p) → メイン処理
    ↓
process_images_inner(p) → ループ処理
    ↓
p.sample() → サンプリング（サブクラスで実装）
    ↓
VAEデコード → 画像に変換
    ↓
後処理（顔修正、カラー補正等）
    ↓
保存
    ↓
Processed オブジェクト返却
```

## 1. StableDiffusionProcessing - 基底クラス

`/mnt/d/stable-diffusion-webui/modules/processing.py:105-351`

### 主要なプロパティ

```python
class StableDiffusionProcessing:
    # 基本パラメータ
    prompt: str                    # プロンプト
    negative_prompt: str           # ネガティブプロンプト
    styles: list                   # スタイルリスト
    seed: int                      # シード値
    subseed: int                   # サブシード
    subseed_strength: float        # サブシード強度
    sampler_name: str              # サンプラー名
    batch_size: int                # バッチサイズ
    n_iter: int                    # イテレーション数
    steps: int                     # サンプリングステップ数
    cfg_scale: float               # CFGスケール
    width: int                     # 幅
    height: int                    # 高さ
    restore_faces: bool            # 顔修復を行うか
    tiling: bool                   # タイル可能にするか
    denoising_strength: float      # デノイズ強度（img2img用）

    # サンプラーパラメータ
    eta: float                     # etaパラメータ
    ddim_discretize: str           # DDIM離散化方式
    s_churn: float                 # sigma churn
    s_tmin: float                  # sigma tmin
    s_tmax: float                  # sigma tmax
    s_noise: float                 # sigma noise
    s_min_uncond: float            # 最小unconditional sigma

    # 設定オーバーライド
    override_settings: dict        # 一時的な設定オーバーライド
    override_settings_restore_afterwards: bool

    # 内部状態
    all_prompts: list              # 全プロンプト（バッチ展開後）
    all_negative_prompts: list     # 全ネガティブプロンプト
    all_seeds: list                # 全シード
    all_subseeds: list             # 全サブシード
    prompts: list                  # 現在のバッチのプロンプト
    seeds: list                    # 現在のバッチのシード
    c: torch.Tensor                # コンディショニング（CLIP出力）
    uc: torch.Tensor               # アンコンディショニング
    sampler: object                # サンプラーインスタンス

    # キャッシュ（クラス変数）
    cached_uc = [None, None]       # アンコンディショニングキャッシュ
    cached_c = [None, None]        # コンディショニングキャッシュ
```

### 重要なメソッド

#### setup_prompts() - プロンプトの準備

`/mnt/d/stable-diffusion-webui/modules/processing.py:305-317`

```python
def setup_prompts(self):
    # プロンプトをバッチサイズ×イテレーション数に展開
    if type(self.prompt) == list:
        self.all_prompts = self.prompt
    else:
        self.all_prompts = self.batch_size * self.n_iter * [self.prompt]

    # ネガティブプロンプトも同様に展開
    if type(self.negative_prompt) == list:
        self.all_negative_prompts = self.negative_prompt
    else:
        self.all_negative_prompts = self.batch_size * self.n_iter * [self.negative_prompt]

    # スタイルを適用
    self.all_prompts = [shared.prompt_styles.apply_styles_to_prompt(x, self.styles)
                        for x in self.all_prompts]
    self.all_negative_prompts = [shared.prompt_styles.apply_negative_styles_to_prompt(x, self.styles)
                                 for x in self.all_negative_prompts]
```

#### setup_conds() - コンディショニングの準備

`/mnt/d/stable-diffusion-webui/modules/processing.py:343-347`

```python
def setup_conds(self):
    # サンプラーがsecond orderか確認
    sampler_config = sd_samplers.find_sampler_config(self.sampler_name)
    self.step_multiplier = 2 if sampler_config and sampler_config.options.get("second_order", False) else 1

    # ネガティブプロンプトのコンディショニング（キャッシュ利用）
    self.uc = self.get_conds_with_caching(
        prompt_parser.get_learned_conditioning,
        self.negative_prompts,
        self.steps * self.step_multiplier,
        [self.cached_uc],
        self.extra_network_data
    )

    # プロンプトのコンディショニング（キャッシュ利用）
    self.c = self.get_conds_with_caching(
        prompt_parser.get_multicond_learned_conditioning,
        self.prompts,
        self.steps * self.step_multiplier,
        [self.cached_c],
        self.extra_network_data
    )
```

**重要**: コンディショニングをキャッシュすることで、同じプロンプトを繰り返し使用する際の計算を削減

#### get_conds_with_caching() - キャッシュ機能付きコンディショニング取得

`/mnt/d/stable-diffusion-webui/modules/processing.py:319-341`

```python
def get_conds_with_caching(self, function, required_prompts, steps, caches, extra_network_data):
    """
    キャッシュを使ってコンディショニングを取得
    同じ引数で以前呼ばれていればキャッシュから返す
    """
    # キャッシュをチェック
    for cache in caches:
        if cache[0] is not None and \
           (required_prompts, steps, opts.CLIP_stop_at_last_layers,
            shared.sd_model.sd_checkpoint_info, extra_network_data) == cache[0]:
            return cache[1]  # キャッシュヒット

    cache = caches[0]

    # 新規計算
    with devices.autocast():
        cache[1] = function(shared.sd_model, required_prompts, steps)

    # キャッシュに保存
    cache[0] = (required_prompts, steps, opts.CLIP_stop_at_last_layers,
                shared.sd_model.sd_checkpoint_info, extra_network_data)
    return cache[1]
```

#### 各種コンディショニング関数

**txt2img_image_conditioning()** - テキストから画像生成用:
```python
def txt2img_image_conditioning(self, x, width=None, height=None):
    self.is_using_inpainting_conditioning = \
        self.sd_model.model.conditioning_key in {'hybrid', 'concat'}

    return txt2img_image_conditioning(self.sd_model, x,
                                      width or self.width,
                                      height or self.height)
```

**img2img_image_conditioning()** - 画像から画像生成用:
- Depth2Image モデル
- Edit モデル
- Inpainting モデル
- UnCLIP モデル
など、モデルタイプに応じて異なるコンディショニングを生成

#### sample() - サンプリング（抽象メソッド）

```python
def sample(self, conditioning, unconditional_conditioning, seeds, subseeds, subseed_strength, prompts):
    raise NotImplementedError()
```

サブクラス（`StableDiffusionProcessingTxt2Img`, `StableDiffusionProcessingImg2Img`）で実装

## 2. process_images() - メイン処理エントリーポイント

`/mnt/d/stable-diffusion-webui/modules/processing.py:597-633`

```python
def process_images(p: StableDiffusionProcessing) -> Processed:
    # スクリプトの前処理コールバック
    if p.scripts is not None:
        p.scripts.before_process(p)

    # 設定のオーバーライドを保存
    stored_opts = {k: opts.data[k] for k in p.override_settings.keys()}

    try:
        # チェックポイントオーバーライド処理
        if sd_models.checkpoint_alisases.get(p.override_settings.get('sd_model_checkpoint')) is None:
            p.override_settings.pop('sd_model_checkpoint', None)
            sd_models.reload_model_weights()

        # 設定を一時的にオーバーライド
        for k, v in p.override_settings.items():
            setattr(opts, k, v)

            if k == 'sd_model_checkpoint':
                sd_models.reload_model_weights()

            if k == 'sd_vae':
                sd_vae.reload_vae_weights()

        # Token Merging 適用
        sd_models.apply_token_merging(p.sd_model, p.get_token_merging_ratio())

        # メイン処理
        res = process_images_inner(p)

    finally:
        # Token Merging 解除
        sd_models.apply_token_merging(p.sd_model, 0)

        # 設定を元に戻す
        if p.override_settings_restore_afterwards:
            for k, v in stored_opts.items():
                setattr(opts, k, v)

                if k == 'sd_vae':
                    sd_vae.reload_vae_weights()

    return res
```

**責務**:
- スクリプトコールバック呼び出し
- 設定の一時的なオーバーライド
- Token Merging の適用/解除
- 設定の復元

## 3. process_images_inner() - メインループ

`/mnt/d/stable-diffusion-webui/modules/processing.py:636-799`

### 処理フロー

```python
def process_images_inner(p: StableDiffusionProcessing) -> Processed:
    """txt2img と img2img の両方で使用されるメインループ"""

    # 初期化
    devices.torch_gc()  # GPU メモリクリーンアップ

    seed = get_fixed_seed(p.seed)
    subseed = get_fixed_seed(p.subseed)

    # タイリング設定
    modules.sd_hijack.model_hijack.apply_circular(p.tiling)
    modules.sd_hijack.model_hijack.clear_comments()

    # プロンプト準備
    p.setup_prompts()

    # シード配列生成
    if type(seed) == list:
        p.all_seeds = seed
    else:
        p.all_seeds = [int(seed) + (x if p.subseed_strength == 0 else 0)
                       for x in range(len(p.all_prompts))]

    # Textual Inversion 読み込み
    if os.path.exists(cmd_opts.embeddings_dir) and not p.do_not_reload_embeddings:
        model_hijack.embedding_db.load_textual_inversion_embeddings()

    # スクリプト処理
    if p.scripts is not None:
        p.scripts.process(p)

    infotexts = []
    output_images = []

    # ★ メインコンテキスト
    with torch.no_grad(), p.sd_model.ema_scope():
        with devices.autocast():
            p.init(p.all_prompts, p.all_seeds, p.all_subseeds)

            # ライブプレビュー用 VAE 読み込み
            if shared.opts.live_previews_enable and opts.show_progress_type == "Approx NN":
                sd_vae_approx.model()

            # UNet 適用
            sd_unet.apply_unet()

        if state.job_count == -1:
            state.job_count = p.n_iter

        # ★★★ イテレーションループ
        for n in range(p.n_iter):
            p.iteration = n

            # 中断/スキップチェック
            if state.skipped:
                state.skipped = False

            if state.interrupted:
                break

            # 現在のバッチのプロンプト/シードを設定
            p.prompts = p.all_prompts[n * p.batch_size:(n + 1) * p.batch_size]
            p.negative_prompts = p.all_negative_prompts[n * p.batch_size:(n + 1) * p.batch_size]
            p.seeds = p.all_seeds[n * p.batch_size:(n + 1) * p.batch_size]
            p.subseeds = p.all_subseeds[n * p.batch_size:(n + 1) * p.batch_size]

            # スクリプト: バッチ前処理
            if p.scripts is not None:
                p.scripts.before_process_batch(p, batch_number=n,
                                                prompts=p.prompts,
                                                seeds=p.seeds,
                                                subseeds=p.subseeds)

            # Extra Networks 解析・有効化
            p.parse_extra_network_prompts()

            if not p.disable_extra_networks:
                with devices.autocast():
                    extra_networks.activate(p, p.extra_network_data)

            # スクリプト: バッチ処理
            if p.scripts is not None:
                p.scripts.process_batch(p, batch_number=n,
                                         prompts=p.prompts,
                                         seeds=p.seeds,
                                         subseeds=p.subseeds)

            # コンディショニング準備
            p.setup_conds()

            # ジョブ名設定
            if p.n_iter > 1:
                shared.state.job = f"Batch {n+1} out of {p.n_iter}"

            # ★★★ サンプリング実行
            with devices.without_autocast() if devices.unet_needs_upcast else devices.autocast():
                samples_ddim = p.sample(
                    conditioning=p.c,
                    unconditional_conditioning=p.uc,
                    seeds=p.seeds,
                    subseeds=p.subseeds,
                    subseed_strength=p.subseed_strength,
                    prompts=p.prompts
                )

            # ★★★ VAEデコード（latent → 画像）
            x_samples_ddim = [
                decode_first_stage(p.sd_model,
                                   samples_ddim[i:i+1].to(dtype=devices.dtype_vae))[0].cpu()
                for i in range(samples_ddim.size(0))
            ]

            # NaNチェック
            for x in x_samples_ddim:
                devices.test_for_nans(x, "vae")

            # テンソルをスタックして正規化
            x_samples_ddim = torch.stack(x_samples_ddim).float()
            x_samples_ddim = torch.clamp((x_samples_ddim + 1.0) / 2.0, min=0.0, max=1.0)

            del samples_ddim

            # lowvram モード: すべてをCPUに移動
            if lowvram.is_enabled(shared.sd_model):
                lowvram.send_everything_to_cpu()

            devices.torch_gc()

            # スクリプト: バッチ後処理
            if p.scripts is not None:
                p.scripts.postprocess_batch(p, x_samples_ddim, batch_number=n)

            # ★★★ 各画像の後処理
            for i, x_sample in enumerate(x_samples_ddim):
                p.batch_index = i

                # NumPy配列に変換
                x_sample = 255. * np.moveaxis(x_sample.cpu().numpy(), 0, 2)
                x_sample = x_sample.astype(np.uint8)

                # 顔修復
                if p.restore_faces:
                    if opts.save and not p.do_not_save_samples and \
                       opts.save_images_before_face_restoration:
                        images.save_image(Image.fromarray(x_sample),
                                          p.outpath_samples, "",
                                          p.seeds[i], p.prompts[i],
                                          opts.samples_format,
                                          info=infotext(n, i), p=p,
                                          suffix="-before-face-restoration")

                    devices.torch_gc()
                    x_sample = modules.face_restoration.restore_faces(x_sample)
                    devices.torch_gc()

                # PIL Image に変換
                image = Image.fromarray(x_sample)

                # スクリプト: 画像後処理
                if p.scripts is not None:
                    pp = scripts.PostprocessImageArgs(image)
                    p.scripts.postprocess_image(p, pp)
                    image = pp.image

                # カラー補正
                if p.color_corrections is not None and i < len(p.color_corrections):
                    if opts.save and not p.do_not_save_samples and \
                       opts.save_images_before_color_correction:
                        image_without_cc = apply_overlay(image, p.paste_to, i, p.overlay_images)
                        images.save_image(image_without_cc,
                                          p.outpath_samples, "",
                                          p.seeds[i], p.prompts[i],
                                          opts.samples_format,
                                          info=infotext(n, i), p=p,
                                          suffix="-before-color-correction")
                    image = apply_color_correction(p.color_corrections[i], image)

                # オーバーレイ適用
                image = apply_overlay(image, p.paste_to, i, p.overlay_images)

                # 画像保存
                if opts.samples_save and not p.do_not_save_samples:
                    images.save_image(image, p.outpath_samples, "",
                                      p.seeds[i], p.prompts[i],
                                      opts.samples_format,
                                      info=infotext(n, i), p=p)

                # infotext 生成
                text = infotext(n, i)
                infotexts.append(text)
                if opts.enable_pnginfo:
                    image.info["parameters"] = text
                output_images.append(image)

                # マスク保存（inpainting用）
                # ... (省略)

        # Extra Networks 非アクティブ化
        if not p.disable_extra_networks:
            extra_networks.deactivate(p, p.extra_network_data)

    # 後処理
    devices.torch_gc()

    # Processed オブジェクト生成
    res = Processed(
        p, output_images,
        p.all_seeds[0], infotext(),
        comments="".join(f"{comment}\n" for comment in comments),
        subseed=p.all_subseeds[0],
        all_prompts=p.all_prompts,
        all_negative_prompts=p.all_negative_prompts,
        all_seeds=p.all_seeds,
        all_subseeds=p.all_subseeds,
        index_of_first_image=0,
        infotexts=infotexts,
    )

    # スクリプト: 最終後処理
    if p.scripts is not None:
        p.scripts.postprocess(p, res)

    # クリーンアップ
    p.close()

    return res
```

## 4. ユーティリティ関数

### create_random_tensors() - ノイズテンソル生成

`/mnt/d/stable-diffusion-webui/modules/processing.py:460-520`

```python
def create_random_tensors(shape, seeds, subseeds=None, subseed_strength=0.0,
                          seed_resize_from_h=0, seed_resize_from_w=0, p=None):
    """
    シードからノイズテンソルを生成
    - バッチごとに異なるシードを使用
    - subseed を使った変動
    - seed_resize を使ったシードリサイズ
    - サンプラー用の追加ノイズ生成
    """
    eta_noise_seed_delta = opts.eta_noise_seed_delta or 0
    xs = []

    # サンプラー用ノイズ準備
    if p is not None and p.sampler is not None and \
       (len(seeds) > 1 and opts.enable_batch_seeds or eta_noise_seed_delta > 0):
        sampler_noises = [[] for _ in range(p.sampler.number_of_needed_noises(p))]
    else:
        sampler_noises = None

    for i, seed in enumerate(seeds):
        noise_shape = shape if seed_resize_from_h <= 0 or seed_resize_from_w <= 0 \
                      else (shape[0], seed_resize_from_h//8, seed_resize_from_w//8)

        # subseed ノイズ
        subnoise = None
        if subseeds is not None:
            subseed = 0 if i >= len(subseeds) else subseeds[i]
            subnoise = devices.randn(subseed, noise_shape)

        # メインノイズ
        noise = devices.randn(seed, noise_shape)

        # subseed をブレンド（spherical linear interpolation）
        if subnoise is not None:
            noise = slerp(subseed_strength, noise, subnoise)

        # seed_resize 処理
        if noise_shape != shape:
            # リサイズロジック（中央配置）
            # ... (省略)

        # サンプラー用追加ノイズ
        if sampler_noises is not None:
            cnt = p.sampler.number_of_needed_noises(p)

            if eta_noise_seed_delta > 0:
                torch.manual_seed(seed + eta_noise_seed_delta)

            for j in range(cnt):
                sampler_noises[j].append(devices.randn_without_seed(tuple(noise_shape)))

        xs.append(noise)

    if sampler_noises is not None:
        p.sampler.sampler_noises = [torch.stack(n).to(shared.device) for n in sampler_noises]

    x = torch.stack(xs).to(shared.device)
    return x
```

### decode_first_stage() - VAEデコード

```python
def decode_first_stage(model, x):
    """Latent を画像に変換"""
    with devices.autocast(disable=x.dtype == devices.dtype_vae):
        x = model.decode_first_stage(x)
    return x
```

## 5. txt2img.py - テキストから画像生成

`/mnt/d/stable-diffusion-webui/modules/txt2img.py:10-70`

```python
def txt2img(id_task, prompt, negative_prompt, prompt_styles, steps, sampler_index,
            restore_faces, tiling, n_iter, batch_size, cfg_scale, seed, subseed,
            subseed_strength, seed_resize_from_h, seed_resize_from_w, seed_enable_extras,
            height, width, enable_hr, denoising_strength, hr_scale, hr_upscaler,
            hr_second_pass_steps, hr_resize_x, hr_resize_y, hr_sampler_index,
            hr_prompt, hr_negative_prompt, override_settings_texts, *args):

    # 設定オーバーライド作成
    override_settings = create_override_settings_dict(override_settings_texts)

    # StableDiffusionProcessingTxt2Img インスタンス生成
    p = processing.StableDiffusionProcessingTxt2Img(
        sd_model=shared.sd_model,
        outpath_samples=opts.outdir_samples or opts.outdir_txt2img_samples,
        outpath_grids=opts.outdir_grids or opts.outdir_txt2img_grids,
        prompt=prompt,
        styles=prompt_styles,
        negative_prompt=negative_prompt,
        seed=seed,
        subseed=subseed,
        subseed_strength=subseed_strength,
        seed_resize_from_h=seed_resize_from_h,
        seed_resize_from_w=seed_resize_from_w,
        seed_enable_extras=seed_enable_extras,
        sampler_name=sd_samplers.samplers[sampler_index].name,
        batch_size=batch_size,
        n_iter=n_iter,
        steps=steps,
        cfg_scale=cfg_scale,
        width=width,
        height=height,
        restore_faces=restore_faces,
        tiling=tiling,
        enable_hr=enable_hr,
        denoising_strength=denoising_strength if enable_hr else None,
        hr_scale=hr_scale,
        hr_upscaler=hr_upscaler,
        hr_second_pass_steps=hr_second_pass_steps,
        hr_resize_x=hr_resize_x,
        hr_resize_y=hr_resize_y,
        hr_sampler_name=sd_samplers.samplers_for_img2img[hr_sampler_index - 1].name if hr_sampler_index != 0 else None,
        hr_prompt=hr_prompt,
        hr_negative_prompt=hr_negative_prompt,
        override_settings=override_settings,
    )

    # スクリプト設定
    p.scripts = modules.scripts.scripts_txt2img
    p.script_args = args

    # コンソール出力
    if cmd_opts.enable_console_prompts:
        print(f"\ntxt2img: {prompt}", file=shared.progress_print_out)

    # スクリプト実行（スクリプトが処理を奪う場合がある）
    processed = modules.scripts.scripts_txt2img.run(p, *args)

    if processed is None:
        # 通常の処理
        processed = processing.process_images(p)

    p.close()
    shared.total_tqdm.clear()

    # 結果を返却
    generation_info_js = processed.js()
    if opts.samples_log_stdout:
        print(generation_info_js)

    if opts.do_not_show_images:
        processed.images = []

    return processed.images, generation_info_js, \
           plaintext_to_html(processed.info), plaintext_to_html(processed.comments)
```

**ポイント**:
- UIからのパラメータを `StableDiffusionProcessingTxt2Img` に変換
- スクリプトシステムとの統合
- `process_images()` を呼び出すだけのシンプルなラッパー

## 6. img2img.py - 画像から画像生成

`/mnt/d/stable-diffusion-webui/modules/img2img.py:100-211`

```python
def img2img(id_task, mode, prompt, negative_prompt, prompt_styles, init_img, sketch,
            init_img_with_mask, inpaint_color_sketch, inpaint_color_sketch_orig,
            init_img_inpaint, init_mask_inpaint, steps, sampler_index, mask_blur,
            mask_alpha, inpainting_fill, restore_faces, tiling, n_iter, batch_size,
            cfg_scale, image_cfg_scale, denoising_strength, seed, subseed,
            subseed_strength, seed_resize_from_h, seed_resize_from_w, seed_enable_extras,
            selected_scale_tab, height, width, scale_by, resize_mode, inpaint_full_res,
            inpaint_full_res_padding, inpainting_mask_invert, img2img_batch_input_dir,
            img2img_batch_output_dir, img2img_batch_inpaint_mask_dir,
            override_settings_texts, *args):

    override_settings = create_override_settings_dict(override_settings_texts)

    is_batch = mode == 5

    # モードに応じて画像とマスクを準備
    if mode == 0:  # img2img
        image = init_img.convert("RGB")
        mask = None
    elif mode == 1:  # img2img sketch
        image = sketch.convert("RGB")
        mask = None
    elif mode == 2:  # inpaint
        image, mask = init_img_with_mask["image"], init_img_with_mask["mask"]
        # マスク処理...
    elif mode == 3:  # inpaint sketch
        # スケッチからマスク生成...
    elif mode == 4:  # inpaint upload mask
        image = init_img_inpaint
        mask = init_mask_inpaint
    else:
        image = None
        mask = None

    # EXIF orientation 処理
    if image is not None:
        image = ImageOps.exif_transpose(image)

    # スケール計算
    if selected_scale_tab == 1 and not is_batch:
        width = int(image.width * scale_by)
        height = int(image.height * scale_by)

    # StableDiffusionProcessingImg2Img インスタンス生成
    p = StableDiffusionProcessingImg2Img(
        sd_model=shared.sd_model,
        outpath_samples=opts.outdir_samples or opts.outdir_img2img_samples,
        outpath_grids=opts.outdir_grids or opts.outdir_img2img_grids,
        prompt=prompt,
        negative_prompt=negative_prompt,
        styles=prompt_styles,
        seed=seed,
        subseed=subseed,
        subseed_strength=subseed_strength,
        seed_resize_from_h=seed_resize_from_h,
        seed_resize_from_w=seed_resize_from_w,
        seed_enable_extras=seed_enable_extras,
        sampler_name=sd_samplers.samplers_for_img2img[sampler_index].name,
        batch_size=batch_size,
        n_iter=n_iter,
        steps=steps,
        cfg_scale=cfg_scale,
        width=width,
        height=height,
        restore_faces=restore_faces,
        tiling=tiling,
        init_images=[image],
        mask=mask,
        mask_blur=mask_blur,
        inpainting_fill=inpainting_fill,
        resize_mode=resize_mode,
        denoising_strength=denoising_strength,
        image_cfg_scale=image_cfg_scale,
        inpaint_full_res=inpaint_full_res,
        inpaint_full_res_padding=inpaint_full_res_padding,
        inpainting_mask_invert=inpainting_mask_invert,
        override_settings=override_settings,
    )

    p.scripts = modules.scripts.scripts_img2img
    p.script_args = args

    if shared.cmd_opts.enable_console_prompts:
        print(f"\nimg2img: {prompt}", file=shared.progress_print_out)

    if mask:
        p.extra_generation_params["Mask blur"] = mask_blur

    # バッチ処理 または 通常処理
    if is_batch:
        process_batch(p, img2img_batch_input_dir, img2img_batch_output_dir,
                      img2img_batch_inpaint_mask_dir, args,
                      to_scale=selected_scale_tab == 1, scale_by=scale_by)
        processed = Processed(p, [], p.seed, "")
    else:
        processed = modules.scripts.scripts_img2img.run(p, *args)
        if processed is None:
            processed = process_images(p)

    p.close()
    shared.total_tqdm.clear()

    generation_info_js = processed.js()
    if opts.samples_log_stdout:
        print(generation_info_js)

    if opts.do_not_show_images:
        processed.images = []

    return processed.images, generation_info_js, \
           plaintext_to_html(processed.info), plaintext_to_html(processed.comments)
```

**ポイント**:
- 5つのモード対応（img2img, sketch, inpaint, inpaint sketch, batch）
- マスク処理の複雑なロジック
- バッチ処理機能

## まとめ

### 画像生成パイプラインの流れ

1. **UIから呼び出し** (`txt2img()` / `img2img()`)
2. **Processing オブジェクト生成** (`StableDiffusionProcessingTxt2Img` / `Img2Img`)
3. **process_images()** - 設定オーバーライド、Token Merging
4. **process_images_inner()** - メインループ
   - プロンプト準備 (`setup_prompts()`)
   - シード生成
   - スクリプトコールバック
   - イテレーションループ:
     - Extra Networks 有効化
     - コンディショニング準備 (`setup_conds()`)
     - **サンプリング** (`p.sample()`)
     - **VAEデコード** (`decode_first_stage()`)
     - 後処理（顔修復、カラー補正）
     - 保存
5. **Processed オブジェクト返却**

### 重要な設計パターン

1. **テンプレートメソッドパターン**: `StableDiffusionProcessing` が基底クラス、`sample()` はサブクラスで実装
2. **キャッシュ**: コンディショニングのキャッシュで計算削減
3. **コールバックシステム**: スクリプトが各フェーズで介入可能
4. **設定オーバーライド**: 一時的な設定変更と復元
5. **デバイス管理**: autocast, torch_gc で効率的なGPU利用
