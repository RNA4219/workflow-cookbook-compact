# 付録G: セキュリティ/プライバシー運用ガイド

> 対象: すべての運用担当者・エージェント実装者。`docs/security/SAC.md` の原則を実務へ反映するための手順と監視ルールを定義する。

## 1. キー管理

- **原則対応**: SAC-1, SAC-3, SAC-9。
- サーバサイドの Secrets 管理は `secrets.{env}.yaml` に一元化し、KMS からの起動時フェッチのみ許可する。
  ローカル `.env` はテスト専用で、本番接続情報を含めない。
- APIキー更新は 90 日サイクルを上限とし、失効ログを `audit/security-key-rotation.log` に記録する。
  更新後は旧キーを 1h 内に失効させる。
- モデル・LLM エンドポイント切替は IaC のマージでのみ許可。アプリ／クライアント設定画面からの切替は常に無効化する。

## 2. ログマスキングと監査

- **原則対応**: SAC-1, SAC-2, SAC-8。
- 監査ログは JSONLines 形式で `/var/log/workflow/audit.log` に集約し、PII/Secrets は `***` へ置換する。
  マスク対象: メールアドレス、アクセストークン、ユーザ識別子（UUID 含む）。
- LLM 応答は HTML エスケープ後に保存し、外部リンクは `rel="noopener"` を強制する。
  違反レスポンスは `security@workflow-cookbook.example` へ自動通知。
- ログ署名には HMAC-SHA256 を使用し、日次で鍵をローテーションする。
  検証スクリプト `tools/audit/verify_log_chain.py` を CI 週次ジョブに組み込み、改ざん検知を実行する。

## 3. データ保持と削除

- **原則対応**: SAC-6, SAC-7, SAC-8。
- 監査ログの保持期間は 180 日。期日を超過したファイルは `tools/audit/purge_logs.py --older-than 180d` で削除し、
  削除レポートを `docs/reports/security-retention.md` に追記する。
- 学習や検証のためのデータセットはバージョン固定し、`datasets/README.md` にハッシュを記録する。
  既知脆弱性が公開された依存バージョンは 24h 以内に差し替える。
- ユーザ削除リクエスト受領時は 72h 以内に対象データを特定し、削除証跡をチケットへ添付する。
  再生成が必要な場合は匿名化済みスナップショットのみ使用する。

## 4. 通信制御とツール実行

- **原則対応**: SAC-3, SAC-4, SAC-5, SAC-10。
- 外部通信は `network/allowlist.yaml` に登録されたドメインへ限定し、CI で差分検証する。
  ホワイトリスト外の通信要求は RUNBOOK の外部通信承認手順（`RUNBOOK.md#outbound-request-approval`）に従い、申請項目・承認者・記録方法を満たした場合のみ許可される。
- ツール実行リクエストは JSON Schema `schemas/tool-request.schema.json` を通過し、`connect-src` は SAC 付録Aの CSP を最低限とする。
  Schema 違反時は失敗ログのみ記録し、リトライは3回まで。
- CSRF/CORS/CSP ヘッダは `security_headers.middleware` で強制し、`pytest -m security_headers` の CI ジョブで逸脱を検出する。
- リリース前は SAST・Secrets・依存・Container の 4 ゲートを `ci/security.yml` で順次実行し、いずれか失敗時は本番リリースを禁止する。

## 5. 運用レビュー

- 月次レビューで本付録の遵守状況を確認し、逸脱がある場合は `TASK.codex.md` のテンプレートで是正タスクを登録する。
- SAC 改訂時は 7 日以内に本付録の該当節を更新し、改訂履歴を `CHANGELOG.md` に追記する。
