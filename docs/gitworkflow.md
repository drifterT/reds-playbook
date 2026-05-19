# reds-playbook Git Workflow (Browser-first)

最終更新: 2026-05-19

## 目的
DrifterT は GitHub をブラウザで運用するため、変更確認は PR ベースで行う。Codex 側は push 後に compare URL を必ず提示する。

## ルール
1. **main への直接 push 禁止**（作業は branch 経由）。
2. **PR 作成・merge は DrifterT 専管**。
3. Codex が変更を push したら、**必ず compare URL を提示**する。
4. compare URL は以下形式を使う。
5. 完了報告では、次の状態を分けて明示する。
   - コミット済みか
   - push 済み（GitHub で可視）か
   - main マージ済みか

## Browser-only 手順（DrifterT）
1. Codex が提示した compare URL を開く。
2. `base: main` / `compare: <branch-name>` を確認する。
3. 差分確認後、`Create pull request` を押す。
4. 必要なら conflict 解消後に `Merge pull request` を実行する。

## Codex 完了報告テンプレ
1. PR 作成 URL（直リンク）
2. 変更要約（2〜4行）
3. Browser 手順（最短 3〜5 ステップ）
4. 状態
   - コミット済み: Yes/No
   - push済み（GitHub可視）: Yes/No
   - mainマージ済み: Yes/No
