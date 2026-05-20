# Keyword Taxonomy

This document is the human-readable version of `data/ameblo/keyword_taxonomy.json`.
It preserves the owner-provided baseball vocabulary and adds stable internal IDs for scripts.

## Categories

### バッティング (`batting`)

Keywords: スイング, 1,2, 重心移動（併進運動と回転運動）, 脚上げ, ノーステップ, 癖の矯正, 回転運動, 筋肉 弛緩と収縮, トスバッティング, ペッパー, 安定したトップの形成, 打席での心得, 3ボール0ストライクは打て, 初球から積極的に行く, 打つ準備, 打つ準備2, 打撃は結果で判断しない方が良い, 目指すは速い打球！強い打球！, 頭が動かないようにとは, 前足のブレーキでスイング加速せよ, 高低打ち分け, トップに入るまでの動作

Maps mainly to: `practice_batting`.

### ピッチング (`pitching`)

Keywords: スローイングの下地, ボールの握り方, 握力, 背骨、胸椎、肩甲骨のストレッチ, 四球恐怖症にさせない, 153km/hと134km/hの投球フォーム

Maps mainly to: background material for throwing mechanics; may support `practice_warmup` when the article is about throwing foundation.

### 守備 (`defense`)

Keywords: ゴロ捕球, 打球との距離感, キャッチボールはその選手の野球感を映す鏡, キャッチボール, まずはボールを追う, 持ち替え, 持ち替えと捕球, タッチプレー時の立ち位置, タッグ（タッチ）の仕方, 対角線キャッチボール実践編, ホーム警戒意識を取り入れたケースノック, 状況に応じた優先度（何を大事にすべきか）, 盗塁、牽制時のショート、セカンドの動き, スローイング, 投球４箇条＋1, ボール2個、４箇所ランダム, ランナーが塁間で止まっている場合, ランダウンプレー, スローイングの下地, スローイングにつなげる捕球, 安定した送球, 3B_送りバント処理, 3B_1塁ベース後方ポップフライ, カバー、バックアップ, カバーの重要性, 1塁手の仕事, 安定したグラブトス, トスでの送球, タッグ（タッチ）, タッグ（タッチ）プレー野手捕球位置, 送球、投球動作, 盗塁時捕手動作のスピード, キャッチャーフライの軌道, キャッチャーの体系, キャッチング, キャッチャーの構え, キャッチャー 盗塁阻止, キャッチャーの送球練習, キャッチャーのタッグ, 1塁手の守備位置とセーフティーリード

Maps mainly to: `practice_warmup`, `practice_two_point_catchball`, `practice_four_point_catchball`, and future case playbook pages.

### 走塁 (`baserunning`)

Keywords: スタート, スタート直後にすること, スライディング, スライディング、ベースへの到達, 加速, 1塁、3塁のダブルスチール, 次の塁を狙う姿勢, ランナーコーチャーの役割, 走塁技術を先行しすぎると相手のミス待ち野球に陥りかねない

Maps mainly to: future running and case-play content. Use as background for current priority pages unless clearly tied to practice flow.

### ルール (`rules`)

Keywords: ルール, 状況判断, 優先度, アウトカウント, ランナー, ケース

Maps mainly to: future case pages and `practice_flow` when the article supports practice sequencing or decision-making.

### メンタル、姿勢 (`mindset`)

Keywords: 意識、思考、指導方法など, ベンチでの過ごし方, 成長の下地を作る, 少年時代に最優先すべきトレーニング, 継続, やるかやらないか, 質とは, 野球は点取りゲーム, 仲間の大切さ, もったいない

Maps mainly to: `policy_player_mindset`, `policy_coach_mindset`, and `practice_flow`.

### 道具 (`equipment`)

Keywords: グローブ, バット, スパイク, 道具, 手入れ

Maps mainly to: future equipment guidance. Use as background unless a section explicitly discusses tools.

### 身体構造/ストレッチ (`body_mobility`)

Keywords: 姿勢, ストレッチ, 効率的な動作を行うためには, 腹筋エクササイズ, スローイングエクササイズ, 股関節ストレッチ, アキレス腱伸ばしの副次目的, スポーツをするための土台, 肘、肩のストレッチ, 肩甲骨周りの筋力強、肩甲骨のストレッチ, 肩甲骨トレーニング, アフターケア, 上腕の動き, 目と肩甲骨, 鉄棒で肩回りのストレッチ, オーバーユースとマルユース

Maps mainly to: `practice_warmup` and background support for throwing and batting mechanics.

### 指導方法 (`coaching_method`)

Keywords: 指導目的、内容の伝達方法, 指導, コーチ, 監督, ヘッドコーチ, 育成, 見る, 伝える, 練習設計, 評価, 原因を見る, 目的を伝える

Maps mainly to: `policy_coach_mindset`, `policy_coach_assignment`, and `practice_flow`.

### 基礎運動能力 (`athletic_base`)

Keywords: 全身筋肉体幹, フットワークトレーニング, ビジョントレーニング, 体幹, 体幹、重心コントロール、走力, 肩甲骨と骨盤の連動を強化, 野球に必要な瞬発系の筋肉

Maps mainly to: `practice_warmup`.

### 戦術、戦略 (`tactics`)

Keywords: エンドラン, 作戦, 戦術, 戦略, 状況判断, 点取りゲーム, 優先度, ケースプレー

Maps mainly to: future case playbook content. Use as `background_only` for current priority pages unless clearly tied to `practice_flow`.

## Duplicate Keywords Detected

- `スローイングの下地`: appears in `pitching` and `defense`.
- `状況判断`: appears in `rules` and `tactics`.
- `優先度`: appears in `rules` and `tactics`.

## Notes

- This taxonomy is for local content planning and article classification.
- It is not linked from public site navigation.
- Future public reference links should use source Ameblo URLs from `article_index.json`, not local raw HTML cache paths.
