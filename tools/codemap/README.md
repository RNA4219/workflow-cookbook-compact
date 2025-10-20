# codemap ツール

`codemap.update` は Birdseye のインデックスおよびカプセルを再生成するコマンドです。現行の `run_update` は指定ターゲットにかかわらず全カプセルの依存関係を再計算し、更新後は Birdseye のトポロジーが一貫した状態に揃います。以下の手順で最新化します。

## 依存

- Python 3.11 以上
- 追加の外部ライブラリは不要（標準ライブラリのみで実行できます）

## 実行手順

1. （任意）仮想環境を作成し、有効化します。
2. リポジトリルートで次のコマンドを実行します。

   ```bash
   # 例: 直近の main との差分から対象カプセルを推測
   python tools/codemap/update.py --since --emit index+caps

   # 例: 明示的にターゲットを指定（従来挙動）
   python tools/codemap/update.py --targets docs/birdseye/index.json,docs/birdseye/caps --emit index+caps
   ```

   - `--since` を指定すると `git diff --name-only <参照>...HEAD` を用いて Birdseye 配下の変更ファイルから対象を自動推定します。参照を省略すると `main` が使われます。
   - `--targets` には再生成したい Birdseye リソースをカンマ区切りで指定します。
   - `--emit` には出力したい成果物（`index` / `caps` / `index+caps`）を指定します。
3. 実行後、以下の成果物が更新されます。
   - `docs/birdseye/index.json`
   - `docs/birdseye/hot.json`（`index` を出力する場合に含まれます）
   - `docs/birdseye/caps/*.json`

## Birdseye 再生成スクリプト

`update.py` は Birdseye の再生成処理を司るエントリーポイントです。各ターゲットの解析や JSON 生成ロジックは `run_update` 内で完結し、インデックス・ホットリスト・カプセルの依存情報を同期します。詳細な処理を追加する際は、既存の例外設計・型安全方針に従って実装してください。
Birdseye ドキュメント（`docs/BIRDSEYE.md` / `docs/birdseye/README.md`）と整合するよう、手順の更新が必要な場合は併せてメンテナンスしてください。

- CLI エントリ: `python tools/codemap/update.py ...`
- 追加の機能を導入する場合は、Birdseye ドキュメント（`docs/BIRDSEYE.md` / `docs/birdseye/README.md`）と整合するよう手順を更新してください。

### Birdseye 再生成の観点

- `run_update` は常に全カプセルの `deps_in` / `deps_out` を再計算します。部分的な入力であっても依存関係の不整合は残りません。
- `docs/birdseye/index.json` を更新する際は、同一ルートにある `hot.json` も `generated_at` が揃うよう自動で書き換えられます。
