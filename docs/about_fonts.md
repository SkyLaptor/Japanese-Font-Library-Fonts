# フォントについて
フォント名と実際に使用しているフォント名や公式へのリンクを記載します。

* 各フォントリソースは `resource/fonts/<fontname>` にフォント利用許諾が確認できる資料と共に保管して下さい。ただし、フォントファイルそのもの(.ttfや.otf)は容量の問題からコミットしないで下さい。
* プロポーショナルと等幅は別フォントとして扱います。例: genshin-gothic, genshin-gothic-mono

|フォントID(和名)|基本|補間|フォールバック|備考|
|:---|:---|:---|:---|:---|
|**skyrim-jp-every**<br>(バニラ日本語Everywhereフォント)|22_Skyrim_JP_BookFont_0805<br>SkyrimSE JP v1.6.1170|なし|[Noto-Sans JP](https://fonts.google.com/noto/specimen/Noto+Sans+JP)|ゲームのEverywhereフォント。<br>恐らく元のフォントは**Noto-Sans JP**と**Futura Condensed**。|
|**skyrim-jp-book**<br>(バニラ日本語Bookフォント)|22_Skyrim_JP_BookFont_0805<br>SkyrimSE JP v1.6.1170|[Tフォント](https://charcenter.tron.org/tfont/)<br>楷書体|[源ノ明朝](https://github.com/adobe-fonts/source-han-serif/tree/release#downloading-source-han-serif)<br>Region-specific Subset OTFs Japanese|ゲームのBookフォント。<br>恐らく元のフォントは**ダイナフォントのDFP魏碑体(W7)**と**Cyrodiil**。|
|**skyrim-jp-handwrite**<br>(バニラ日本語Handwriteフォント)|5_Skyrim_JP_HandWriteFont_0805<br>SkyrimSE JP v1.6.1170|[英椎行書](https://www.ac-font.com/jp/detail_jb_006.php)|[源ノ明朝](https://github.com/adobe-fonts/source-han-serif/tree/release#downloading-source-han-serif) ※Region-specific Subset OTFs|ゲームのHandwrittenフォント。<br>恐らく元のフォントは**ダイナフォントのDFP行書体(W5)**と**何らかの英字フォント**。|
|**source-han-sans**<br>(源ノ角ゴシック)|[源ノ角ゴシック](https://github.com/adobe-fonts/source-han-sans/tree/release)<br>Region-specific Subset OTFs Japanese|なし|なし|主にゴシック系フォントのフォールバック用途<br>OTFしか提供されていないため、要TTF変換。|
|**noto-sans**<br>(Noto-Sans JP)|[Noto-Sans JP](https://fonts.google.com/noto/specimen/Noto+Sans+JP)|なし|なし|主にゴシック系フォントのフォールバック用途<br>バニラのEverywhereフォントと非常に似ている。|
|**mplus**<br>(M PLUS)|[M PLUS](https://github.com/coz-m/MPLUS_FONTS)<br>MPLUS1|なし|[源真ゴシック](http://jikasei.me/font/genshin/) Bold||
|**genshin-gothic**<br>(源真ゴシック)|[源真ゴシック](http://jikasei.me/font/genshin/)|なし|なし||
|**hackgen-mono**<br>(白源)|[白源](https://github.com/yuru7/HackGen)<br>通常版|なし|なし||
|**source-han-serif**<br>(源ノ明朝)|[源ノ明朝](https://github.com/adobe-fonts/source-han-serif/tree/release#downloading-source-han-serif)<br>Region-specific Subset OTFs Japanese|なし|なし|主に明朝系フォントのフォールバック用途。<br>OTFしか提供されていないため、要TTF変換。|
|**shippori-mincho**<br>(しっぽり明朝)|[しっぽり明朝](https://fontdasu.com/shippori-mincho/)|なし|なし||
|**genjyuu-gothic**<br>(源柔ゴシック)|[源柔ゴシック](http://jikasei.me/font/genjyuu/)|なし|なし||
|**cinecaption**<br>(しねきゃぷしょん)|[しねきゃぷしょん](https://www.vector.co.jp/soft/data/writing/se314690.html)|なし|[源柔ゴシック](http://jikasei.me/font/genjyuu/)||
|**jiyucho**<br>(じゆうちょう)|[じゆうちょうフォント](https://yokutobanaitori.web.fc2.com/)|なし|[源柔ゴシック](http://jikasei.me/font/genjyuu/) Heavy||
|**tfont-kaisho**<br>(Tフォント楷書)|[Tフォント](https://charcenter.tron.org/tfont/)<br>楷書体|なし|[源ノ明朝](https://github.com/adobe-fonts/source-han-serif/tree/release#downloading-source-han-serif)<br>Region-specific Subset OTFs Japanese||
|**lore-friendly-every**<br>(ロアフレンドリーEverywhere)|[Lore-friendly fonts - font_jp_skyrim](https://www.nexusmods.com/skyrim/mods/46205)<br>Skyrim_n|[英椎行書](https://www.ac-font.com/jp/detail_jb_006.php)|[源柔ゴシック](http://jikasei.me/font/genjyuu/)|恐らく元のフォントは**ダイナフォントのDFP郭泰碑(W4)またはDFP隷書体**。<br>元MODはeverywhereとbookに使用している。|
|**lore-friendly-handwrite**<br>(ロアフレンドリーHandwrite)|[Lore-friendly fonts - font_jp_skyrim](https://www.nexusmods.com/skyrim/mods/46205)<br>Skyrim_n2|[英椎行書](https://www.ac-font.com/jp/detail_jb_006.php)|[源ノ明朝](https://github.com/adobe-fonts/source-han-serif/tree/release#downloading-source-han-serif)<br>Region-specific Subset OTFs Japanese|恐らく元のフォントは**ダイナフォントの行書体系**。<br>元MODはhandwriteに採用されている。|
|**apricot**<br>(あんずもじ)|[あんずもじ](https://apricot.ciao.jp/)|なし|[源柔ゴシック](http://jikasei.me/font/genjyuu/)||
|**nyashi-kai2**<br>(にゃしいフォント改二)|[にゃしいフォント改二](https://yokutobanaitori.web.fc2.com/tegakifont.html#tegakifont4)|なし|[源柔ゴシック v20150607](http://jikasei.me/font/genjyuu/)||
|**acgyosyo**<br>(英椎行書)|[英椎行書](https://www.ac-font.com/jp/detail_jb_006.php)|なし|[源ノ明朝](https://github.com/adobe-fonts/source-han-serif/tree/release#downloading-source-han-serif)<br>Region-specific Subset OTFs Japanese||
