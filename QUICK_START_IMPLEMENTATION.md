# ⚡ クイックスタートガイド - 即座に開始

**このファイルを開いたら、すぐに実装を開始できます**

---

## 🎯 目標の再確認（5秒で理解）

```
Nano Bananaの機能 → Stable Diffusionで再現
キャラクター一貫性95% → 完全無料・ローカルで実現
```

---

## 📋 今すぐやること（3ステップ）

### ステップ1: WebUI起動（2分）

**Windows コマンドプロンプト**:
```cmd
D:
cd stable-diffusion-webui
webui-user.bat
```

**確認**:
- ✅ http://localhost:7860 が開くか
- ✅ コンソールに "RTX 5060" と表示されるか

---

### ステップ2: 環境確認（3分）

**ブラウザで確認**:
1. txt2img タブを開く
2. ControlNet セクションを展開
3. 以下が存在するか確認:
   - ✅ Preprocessor に "openpose" がある
   - ✅ Model に "control_v11p_sd15_openpose" がある

**もし ControlNet がない**:
```
Extensions タブ → Available タブ → "controlnet" で検索
→ Install → WebUI再起動
```

---

### ステップ3: 次の行動を決定（1分）

**選択肢A: まずテストしたい**
→ 既存の機能で高品質アニメ生成をテスト
→ 「かんたん編集」タブで元の写真をアニメ化

**選択肢B: すぐIP-Adapterを入れたい**
→ ファイルダウンロード開始
→ HANDOFF_IMPLEMENTATION_2025_11_09.md のステージ2へ

**選択肢C: 全体を理解してから進めたい**
→ docs/NANO_BANANA_CHARACTER_CONSISTENCY_GUIDE.md を読む

---

## 🔗 重要なファイルへのショートカット

### 完全な手順が知りたい
→ `HANDOFF_IMPLEMENTATION_2025_11_09.md`（このセッションの引き継ぎ）

### すぐ使える設定が欲しい
→ `docs/QUICK_REFERENCE_CHARACTER_CONSISTENCY.md`

### 実例を見たい
→ `docs/WORKFLOW_EXAMPLES_CHARACTER_CONSISTENCY.md`

### 技術的な詳細が知りたい
→ `docs/NANO_BANANA_CHARACTER_CONSISTENCY_GUIDE.md`

---

## ⚠️ トラブルが起きたら

### WebUIが起動しない
```cmd
# WSLから試す
cd /mnt/d/stable-diffusion-webui
./webui.sh
```

### ControlNetが見つからない
```
Extensions → Installed → sd-webui-controlnet を確認
なければ、Available から Install
```

### RTX 5060が認識されない
```
コンソールログを確認
"Using GPU: ..." の部分を見る
```

---

## 📞 質問があるとき

**「どこから始めればいい？」**
→ このファイルのステップ1から

**「全体像を知りたい」**
→ HANDOFF_IMPLEMENTATION_2025_11_09.md を読む

**「設定値が知りたい」**
→ docs/QUICK_REFERENCE_CHARACTER_CONSISTENCY.md を見る

**「エラーが出た」**
→ HANDOFF_IMPLEMENTATION_2025_11_09.md のトラブルシューティング

---

## 🎯 成功までの最短ルート（時系列）

```
今（5分）:
  WebUI起動 → 動作確認

30分後:
  IP-Adapter ダウンロード → インストール

1時間後:
  キャラクター一貫性テスト → 成功確認

2時間後:
  ポーズ変更テスト → 服装変更テスト

3時間後:
  元画像のアニメ化 → 完成🎉
```

---

## ✅ 今すぐ実行するコマンド

```cmd
D:
cd stable-diffusion-webui
webui-user.bat
```

**これだけ！**

---

**作成**: 2025-11-09
**目的**: 次のセッションで迷わず開始できるように
