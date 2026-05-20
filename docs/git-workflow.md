# reds-playbook Git Workflow

**作成**: 2026-05-19 (火) JST
**Last updated**: 2026-05-20 (水) JST
**Maintained by**: Codex / DrifterT
**位置付け**: reds-playbook repo における Codex のローカル編集、確認、commit、push の標準手順を定義する。

---

## §1 全体方針

reds-playbook repo (`drifterT/reds-playbook`) は、GitHub Pages 向けの静的サイトとして運用する。

Codex は DrifterT の指示に基づき、ローカル環境で以下の一連の作業を担当する。

1. ファイル編集
2. 必要に応じたローカル確認
3. `git status`
4. `git add .`
5. 適切な commit message で `git commit`
6. `git push origin main`

GitHub Pages の deployment 設定は変更しない。

---

## §2 対象 repository

- Repository: `drifterT/reds-playbook`
- Local path: `~/Documents/Codex/reds-playbook`
- Default branch: `main`
- Remote: `origin`
- Deploy: GitHub Pages（repository root から配信）

---

## §3 Codex の作業範囲

Codex は以下を通常作業として扱う。

- `index.html` などの静的 HTML 編集
- `docs/` 配下の設計メモ・運用メモ更新
- `README.md` 更新
- 既存ページ間のリンク修正
- モバイル表示、リンク、静的配信に関する軽微な確認
- 必要な場合のローカル static server による確認

Python script、CSV / JSON 生成、その他コード実行を伴う作業も、DrifterT の指示がある場合は Codex がローカルで実行する。

---

## §4 標準手順

Codex は編集タスクを完了したら、原則として次の順序で作業を閉じる。

```bash
git status
git add .
git commit -m "<appropriate message>"
git push origin main
```

commit message は変更内容に合わせて Codex が判断する。

例:

- `Update static site`
- `Update git workflow`
- `Improve practice menu navigation`
- `Fix mobile layout`

---

## §5 確認と報告

Codex は作業後に以下を報告する。

- 変更した主なファイル
- 実行した確認
- commit hash
- push 成否
- push が失敗した場合の正確なエラー

`git push origin main` が実際の認証エラーまたはネットワークエラーで失敗した場合のみ、DrifterT に状況確認や追加対応を依頼する。

---

## §6 認証

GitHub credential は macOS Keychain に保存されている前提とする。

```bash
git credential.helper osxkeychain
```

Codex は通常、認証済みのローカル git 環境を使って `git push origin main` まで実行する。

---

## §7 禁止事項

Codex は以下を行わない。

- GitHub Pages の deployment 設定変更
- repository remote の不要な変更
- nested project folder の作成
- DrifterT の明示指示がない破壊的操作
- unrelated change の revert

---

**Status**: v2 Codex local workflow
**Next**: 運用フィードバックを反映
