# 開発者向けガイド

## プロジェクト概要

`dendro-text` は、テキストファイル間の Damerau-Levenshtein 編集距離を使って、類似度のデンドログラムを表示する Python CLI パッケージです。主なエントリーポイントは `dendro_text.main:main` で、インストール後は `dendro-text` コマンドとして実行できます。

## リポジトリ構成

- `dendro_text/`: パッケージ本体
  - `main.py`: CLI 引数処理、前処理、距離計算、デンドログラム生成の統合
  - `dld.py`: Damerau-Levenshtein 距離と編集系列
  - `ts.py`: テキストのトークン化と Unicode ブロック処理
  - `commands.py`: 前処理・diff などのコマンド処理
  - `print_tree.py`: ASCII／罫線文字によるツリー表示
  - `Blocks.txt`: Unicode ブロック定義（パッケージデータ）
- `tests/`: Python の `unittest` テストと CLI のシェルテスト
- `dev-notes/`: 開発セッションの記録、設計判断、引き継ぎメモ
- `docs/images/`: README で使用する画像
- `pyproject.toml`: パッケージメタデータ、依存関係、tox 設定

## 開発環境

- 対応 Python: 3.8 以上（CI では 3.8〜3.12 を検証）
- 開発時は仮想環境を使用し、パッケージを editable install してください。

```sh
python -m pip install -e .
```

## テスト

通常の Python テストは次のコマンドで実行します。

```sh
python -m unittest discover
```

対応バージョンをまとめて確認する場合は tox を使います。

```sh
tox
```

CI と同じ CLI の回帰テストも必要に応じて実行してください。

```sh
bash tests/test_a.sh
bash tests/test_N0.sh
bash tests/test_N3.sh
bash tests/test_identical_files.sh
```

## 実装上の注意

- CLI の出力形式はシェルテストで厳密に比較されています。ツリー記号、区切り文字、ファイル順、重複ファイルの扱いを変更する場合は、関連するテストも同時に更新してください。
- デフォルトの比較単位は文字種の変化で分割したトークンです。`-c`（文字単位）、`-l`（行単位）、`-t`（Pygments による言語トークン）との違いを壊さないようにしてください。
- `--prep` は外部コマンドを使って入力を順に前処理します。複数指定時は一時ファイルを介して処理されるため、元ファイルを直接変更しないでください。
- `Blocks.txt` は実行時に参照されるパッケージデータです。Unicode ブロック処理を変更しない限り、内容を自動生成・整形しないでください。
- Numba と matplotlib は任意依存です。コア機能はこれらが未導入の環境でも動作させてください。
- 公開 API や CLI の互換性を優先し、既存コードのスタイルに合わせて小さく変更してください。

## 変更時の確認

変更後は、少なくとも `python -m unittest discover` と変更箇所に対応する CLI シェルテストを実行してください。依存関係、CLI オプション、パッケージデータ、公開動作を変更した場合は README と `pyproject.toml` の整合性も確認してください。

## バージョン管理

バージョン番号は Semantic Versioning（SemVer）の形式 `MAJOR.MINOR.PATCH` で管理してください。互換性を壊す変更では `MAJOR`、後方互換性のある機能追加では `MINOR`、後方互換性のある修正では `PATCH` を上げます。公開前のプレリリースやビルドメタデータを付ける場合も SemVer の形式に従ってください。

パッケージのバージョンは `dendro_text/VERSION` を正とし、バージョンを変更するときはこのファイルを更新してください。

## 開発メモ

開発中の設計判断、調査結果、コマンドの実行結果、未完了の作業、次の作業への引き継ぎは `dev-notes/` に記録してください。開発メモはユーザー向け README や公開リリースノートとは分け、内部の開発履歴として扱います。

- 通常のセッション記録は `dev-notes/session-YYYY-MM-DD.md` に追記します。
- 同じ日に複数の独立したテーマを扱う場合は、必要に応じて `session-YYYY-MM-DD-短い題名.md` のような補助ファイルを作成します。
- セッション開始時に日付と対象範囲を記載し、作業終了時に結果、検証内容、未完了事項を追記します。
- 記録は簡潔に保ち、重要な判断には `Topic`、`Decision`、`Rationale`、`Validation`、`Result` を使います。
- コマンドの全文ログは必要な場合だけ記録し、出力は要点に絞ります。秘密情報や不要な個人パスは記載しないでください。
- 大きな設計判断や引き継ぎ事項は、次回作業者が再調査せずに状況を理解できるよう、関連ファイルと次の作業を明記します。
