# 開発ガイドライン

## はじめに
本プロジェクトへの貢献を検討いただきありがとうございます。
メンテナーの負担軽減と品質維持のため、以下のルールを遵守してください。

* **Issue優先**: 大きな変更の前に必ずIssueで提案し、合意を得てください。
* **最小PR**: 変更は可能な限り最小単位に分割してください。
* **品質管理**: ローカルでのビルドおよびテスト通過（`uv run -m pytest`）は必須です。

## リポジトリ運用フロー
GitLab-Flowを採用しています。詳細は [開発ワークフロー詳細](docs/developer/workflow.md) を参照してください。

1. `main` ブランチをベースに、`feature/issue-番号` 等の作業ブランチを作成。
2. レビュー承認およびCI通過後に `main` へマージ。
3. `main` -> `pre-production` (仮公開) -> `production` (本公開) の順でリリース。

## フォルダ構成
* **contents**: 生のフォントTTFやSWF等の処理対象物。
* **docs**: 利用者向け、開発者向けドキュメント及びドキュメント用リソース。
* **data**: サブセットデータやテンプレート。
* **src**: プログラムソースコード。
* **tests**: テスト用コード。
* **build / dist**: ビルド用一時フォルダ（コミット対象外）。

## 詳細ドキュメント
開発に必要な詳細な手順は、`docs/developer/` 以下の各ドキュメントを参照してください。

* [**環境構築ガイド**](docs/developer/setup.md): UV, FFDecのセットアップ、Git LFSの運用ルール、JREチェック。
* [**アセット準備ガイド**](docs/developer/asset_preparation.md): バニラフォントの抽出、ベースフォント・テンプレートSWFの作成手順。
* [**リソース作成ガイド**](docs/developer/data_resources.md): サブセットテキスト、`validNameChars` の生成。
* [**技術パッチ作成ガイド**](docs/developer/technical_patch_guide.md): UIバグ修正、SkyUI/MCM向け専用パッチの作成詳細。
* [**ワークフロー詳細**](docs/developer/workflow.md): フォント加工レシピの作成フロー、紹介画像の生成。

## 開発リファレンス
* [fontTools Documentation](https://fonttools.readthedocs.io/en/latest/)
* [FontForge Scripting](https://fontforge.org/docs/scripting/scripting.html)
