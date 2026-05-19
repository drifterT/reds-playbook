# reds-playbook Git Workflow

**作成**: 2026-05-19 (火) JST
**Last updated**: 2026-05-19 (火) JST
**Maintained by**: Claude（起案）/ DrifterT（承認）
**位置付け**: reds-playbook repo への書き込み経路の使い分け、branch 命名、PR / merge 権限、write 操作の確認手順を定義する。

---

## §1 全体方針

reds-playbook repo (`drifterT/reds-playbook`) への書き込みは、以下を必ず遵守する。

| 共通制約 |
|---|
| **main への直接 push 禁止** |
| **PR 作成・merge は DrifterT 専管** |
| **書き込みは branch に対してのみ行う** |
| **write 操作は DrifterT の明示指示が必要**（§5.3） |

書き込み経路は2つ（Route A / Route B）。選択基準は「コード実行が必要か」（§4）。

---

## §2 Route A: Claude（GitHub MCP）push

Claude が claude.ai またはデスクトップアプリの GitHub MCP 経由で branch に push する経路。

### §2.1 対象範囲

全 directory。主に次のもの:

- `docs/`（設計メモ・規約・用語定義）
- サイトの HTML（`index.html` ほか）
- Playbook Text / ケースプレーの md・HTML
- `README.md`

**注**: Claude は MCP 経由のため **コード実行できない**。Python script や生成データが絡むタスクは Route B（§3）。

### §2.2 Branch 命名規約

```
claude/<topic>-<version>
```

例:

- `claude/playbook-design-v0`
- `claude/up-cards-v1`
- `claude/readme-update-v0`

### §2.3 適用条件

- 設計メモ・規約 md の追加・修正
- ドリルカード／Playbook Text の md コンテンツ追加
- サイト HTML の編集
- 既存ファイルの部分修正（patch）

### §2.4 手順

1. Claude が起案（チャット内）
2. **DrifterT 確認**（write 操作は明示指示後のみ — §5.3）
3. Claude が branch 作成 + push
4. Claude が compare URL を提示:

   ```
   https://github.com/drifterT/reds-playbook/compare/main...<branch-name>
   ```

5. DrifterT が PR 作成 + merge 判断

### §2.5 禁止事項

- main 直接 push
- PR 作成・merge

---

## §3 Route B: Claude Code push

Claude Code が CLI 経由で branch に push する経路。

### §3.1 対象範囲

全 directory。主に次のもの:

- Ameblo 記事の分類パイプライン（Python script）
- 生成データ（CSV / JSON、`playbook_index.json` など）
- コード実行を伴う成果物

### §3.2 Branch 命名規約

```
claude-code/<topic>-<version>
```

### §3.3 適用条件

- Python script の作成・実行（分類パイプライン等）
- chart / CSV / JSON の生成
- コード実行が必要なタスク全般

### §3.4 手順

1. DrifterT が Claude Code に指示
2. Claude Code が CLI で実装 + branch 作成 + push
3. Claude Code が compare URL を提示
4. DrifterT が PR 作成 + merge

### §3.5 禁止事項

- main 直接 push
- PR 作成・merge

---

## §4 Route 選択指針

一次基準は「**コード実行が必要か**」。

| 状況 | 推奨 Route |
|---|:---:|
| 設計メモ・規約 md の配置 | A |
| ドリルカード / Playbook Text の md 追加 | A |
| サイト HTML の編集 | A |
| 既存ファイルの部分修正 | A |
| Ameblo 分類パイプライン（Python） | B |
| CSV / JSON の生成 | B |

---

## §5 重要原則

### §5.1 main への直接 push 禁止

両 Route 共通。書き込みは必ず branch に対して行う。

### §5.2 PR 作成・merge は DrifterT 専管

Claude も Claude Code も PR 作成・merge は行わない。GitHub MCP に PR 作成・merge の tool が含まれていても使わない。

### §5.3 write 操作は DrifterT の明示指示が必須

Claude が GitHub へ write 系操作を実行する前に、必ず以下を提示して DrifterT の GO を得る。

1. 対象 path
2. branch 名
3. commit message（案）
4. 内容サマリ

write 系 tool: `push_files` / `create_or_update_file` / `create_branch` / `delete_file` など。
read 系 tool（`get_file_contents` / `list_commits` / `search_*` 等）は §5.3 の対象外、自由に使用可。

### §5.4 compare URL の必須提示

push 後は必ず compare URL を DrifterT に提示する。

```
https://github.com/drifterT/reds-playbook/compare/main...<branch-name>
```

### §5.5 Route 自動切替なし

Claude が独自判断で Route を切り替えない。DrifterT の指示に従う。

---

**Status**: v1 初版
**Next**: 運用フィードバックを反映
