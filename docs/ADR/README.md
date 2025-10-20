# Architecture Decision Records (ADR)

短時間で意思決定の背景を共有するためのフォルダです。
設計方針が変わるPRでは、以下テンプレートで1ファイルを追加してください。

```text
# ADR-XXX: タイトル
- 日付: YYYY-MM-DD
- 変更理由: 背景や課題
- 影響範囲: 影響を受けるモジュール/チーム
- 決定: 合意した方針
```

命名ルール:

- `ADR-<連番>.md` とし、連番は昇順で管理
- PR内の主要な設計判断ごとに1ファイル

レビューフロー:

1. PR内でテンプレを埋める
2. レビューで補足が出た場合は同じファイルに追記
3. マージ後も履歴として残す

意思決定の根拠を10秒で参照できるよう、記述は簡潔にまとめてください。

## 主要カテゴリと代表 ADR

ADR は判断の粒度に応じて以下のカテゴリに整理し、同一カテゴリの判断は代表 ADR 番号を起点に連番で管理します。
更新時は `CHECKLISTS.md` の[Release](../../CHECKLISTS.md#release)を参照し、レビューテンプレに ADR と関連資料を添付してください。

<!-- markdownlint-disable-next-line MD033 -->
<a id="adr-core-policy"></a>
### 基盤方針（代表: ADR-001）

アーキテクチャ全体の前提・制約を定義します。
`BLUEPRINT.md` の[Constraints / Assumptions][blueprint-constraints]と同期し、変更時は本テンプレートで根拠と影響範囲を明記してください。

<!-- markdownlint-disable-next-line MD033 -->
<a id="adr-milestone-dod"></a>
### マイルストーン DoD（代表: ADR-010）

ロードマップ上の主要マイルストーンに対する Done の判断基準を管理します。
`CHECKLISTS.md` の[Release][checklists-release]で確認した証跡を PR に添付し、ADR へ反映してください。

<!-- markdownlint-disable-next-line MD033 -->
<a id="adr-operations-governance"></a>
### 運用ガバナンス（代表: ADR-020）

セキュリティ・SLO など運用統制方針の変更を記録します。`SECURITY.md` や `RUNBOOK.md` を更新した場合は、その差分へのリンクを ADR と併せてレビューに提出してください。

[blueprint-constraints]: ../../BLUEPRINT.md#3-constraints--assumptions
[checklists-release]: ../../CHECKLISTS.md#release
