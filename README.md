# Japanese Font Library - Fonts
[Japanese Font Library](https://github.com/SkyLaptor/Japanese-Font-Library) のフォント周りのサブプロジェクトです。  
好きなフォントを用意してスカイリム用に最適化することが出来ます。


## 動作環境
* [JPEXS Free Flash Decompiler - FFDec](https://github.com/jindrapetrik/jpexs-decompiler)
フォントファイルをSWFに埋め込むために必要です。   

* [UV](https://docs.astral.sh/uv/)
スクリプトを動作させるために必要です。ご利用のOSに応じて以下を参考にセットアップして下さい。  
https://docs.astral.sh/uv/getting-started/installation/  


## 使い方（簡易版）
1. ローカルにこのリポジトリをクローンするかダウンロードして下さい。

2. コマンドラインにてリポジトリを配置した場所に移動し、以下のコマンドを実行してください。

```
$ uv venv
$ uv sync
```

3. 好きなTTFフォントを用意し、 `assets/fonts/任意のフォント名/フォントファイル.ttf` に配置します。

形式がOTFの場合は、以下のコマンドでTTFに変換してください。OTFファイルと同じところにTTFファイルが出来上がります。
※公式がTTFを配布している場合はなるべくそちらを使用して下さい。不具合が発生する場合があります。

```
$ uv run otf2xml ./assets/fonts/任意のフォント名/フォントファイル.otf
```

4. 次のコマンドを実行します。

```
$ uv run ./src/convert_for_skyrim.py ./assets/fonts/任意のフォント名/フォントファイル.ttf --size every --subset ./data/subsets/subset_jp_skyrim.txt
```

これで`build` ディレクトリ内に `フォントファイル名_every.ttf` というファイルが出来上がります。 
このコマンドで何が行われているかというと、スカイリムデフォルトのEverywhere日本語フォントに文字のサイズを合わせ、バニラスカイリムが表示可能な文字だけのサブセットに変換されています。大抵の場合、フォントそのままではバニラスカイリムのフォントより若干大きいです。  
他にもサイズ基準とするバニラフォントを変更したり、長形(細長い形)にしたり、サブセットを変えたりできます。詳細は `$ uv run ./src/convert_for_skyrim.py -h` を実行してヘルプを確認して下さい。

5. 出来上がったTTFフォントをSWFに埋め込みます。
   1. FFDecを起動します。
   2. `assets/swf/skyrim/fonts_template.swf` をFFDecにドラッグ＆ドロップして開きます。
   3. 左のツリーから「フォント」を展開し、中にある「DefineFont3」を選択します。
   4. 右下にある「埋め込む」を押します。
   5. TTFファイルを選択し、最適化したフォントファイルを選択します。
   6. 「全ての文字」にチェックを入れ、「OK」を押します。上書き警告が出てきた場合は、「全て上書き」を選択します。
   7. このままだとテンプレートを変更してしまうため、左上の「名前を付けて保存」から `build` ディレクトリの中に保存します。 `fonts_フォント名_every.swf` とかにすると良いでしょう。保存後はFFDecを閉じて下さい。

一連の作業は、FFDecをコマンドライン化している場合以下のコマンドで実行可能です。

```
$ ffdec-cli.exe -replace fonts_template.swf ./build/fonts_フォント名_every.swf 1 最適化済フォントファイル
```

6. フォントを埋め込んだSWFの各種タグ情報を変更します。
   1. FFDecを起動します。
   2. `build` 内にあるフォントを埋め込んだSWFをFFDecにドラッグ＆ドロップして開きます。
   3. 左のツリーから「フォント」を展開し、中にある「DefineFont3」を選択します。
   4. 右下にある「編集」を押します。
   5. 編集ボタンのすぐ上にある「タグ内のフォント名」を任意の英数字の名前にします。変更後は「保存」ボタンを押して下さい。
   6. 左のツリーから「フォント」を展開し、中にある「DefineFont3」をさらに展開し、「DefineFontName」を選択します。
   7. 右下にある「編集」を押します。
   8. 編集ボタンの上にある「fontName:String」をタグ内のフォント名と同じものにします。変更後は「保存」ボタンを押して下さい。
   9. 左のツリーから「その他」を展開し、中にある「ExportAssets」を選択します。
   10. 右下にある「編集」を押します。
   11. 編集ボタンの上にある「assets」を展開し、中にある「tag[0]: U16～」のStringの値ををタグ内のフォント名と同じものにします。変更後は「保存」ボタンを押して下さい。

7. `Skyrimインストールディレクトリ\Data\Interface` の中に作成したフォントSWFを移動またはコピーします。

8. `Skyrimインストールディレクトリ\Data\Interface\fontconfig.txt または fontconfig_ja.txt` を開き、以下の変更をします。
   1. フォント読み込み設定: 上部に `fontlib "Interface\フォントファイル.swf"` を追記します。
   2. フォント割り当て設定: 中部にある `map "フォントマップ名" = "フォント名" Normal` を書き換えます。
      * `フォントマップ名` は変更せずに、 `フォント名` の部分を作成したフォント名変更します。
        * スタートメニュー、インベントリ、字幕といった大部分に適用したい場合は、以下のマップのフォント名を変更します。
          * $StartMenuFont
          * $DialogueFont
          * $EverywhereFont
          * $EverywhereBoldFont
          * $EverywhereMediumFont
          * $CClub_Font
          * $CClub_Font_Bold
          * Times New Roman
          * $CreditsFont
        * 主に本に適用したい場合は、以下のマップのフォント名を変更します。
          * $SkyrimBooks
        * 主に手紙やメモに適用したい場合は、以下のマップのフォント名を変更します。
          * $HandwrittenFont
          * $HandwrittenBold

9. ゲームを起動し、フォントが適用されたことを確認します。
 