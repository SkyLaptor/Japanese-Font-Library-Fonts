# 日本語フルサブセットについて

## 作成手順
1. スクリプトを実行して出力する。

```cmd:
$ uv run common --action generate_subset_jp_full -o .\data\subsets\subset_jp_full.txt                                                                                
生成したサブセットを出力しました。: data\subsets\subset_jp_full.txt
```

> [!NOTE]
> `common.generate_subset_jp_full()` では可能な限り日本語圏で表示しうる文字列を生成していますが、> もし不足が出た場合にはソースの `extra_unicodes` にUnicode指定で追加することを検討します。