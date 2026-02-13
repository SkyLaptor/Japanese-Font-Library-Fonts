from dataclasses import dataclass, field
from typing import Optional

from fontTools.ttLib import TTFont


@dataclass
class NameRecord:
    name_id: Optional[int] = None
    label: Optional[str] = None
    value: Optional[str] = None

    def __str__(self):
        output = f"[NAMEレコード] {self.name_id}, {self.label}, {self.value}\n"
        return output


@dataclass
class FontInfo:
    created_time: Optional[str] = None
    modified_time: Optional[str] = None
    glyph_count_all: Optional[int] = None
    glyph_count_uni: Optional[int] = None
    upm: Optional[int] = None
    os2_vendorid: Optional[str] = None
    os2_winascent: Optional[int] = None
    os2_windescent: Optional[int] = None
    os2_typoascender: Optional[int] = None
    os2_typodescender: Optional[int] = None
    os2_typo_linegap: Optional[int] = None
    os2_use_typometrics: Optional[bool] = None
    hhea_ascent: Optional[int] = None
    hhea_descent: Optional[int] = None
    hhea_linegap: Optional[int] = None
    name_records: list[NameRecord] = field(default_factory=list)

    def __str__(self):
        output = "[フォント情報]\n"
        output += f"作成日時: {self.created_time}\n"
        output += f"更新日時: {self.modified_time}\n"
        output += f"総グリフ数: {self.glyph_count_all}\n"
        output += f"Unicode値を持つグリフ数: {self.glyph_count_uni}\n"
        output += f"UPM: {self.upm}\n"
        output += f"OS/2 ベンダーID: {self.os2_vendorid}\n"
        output += f"OS/2 WinAscent: {self.os2_winascent}\n"
        output += f"OS/2 WinDescent: {self.os2_windescent}\n"
        output += f"OS/2 TypoAscender: {self.os2_typoascender}\n"
        output += f"OS/2 TypoDescender: {self.os2_typodescender}\n"
        output += f"OS/2 Typo LineGap: {self.os2_typo_linegap}\n"
        output += f"OS/2 Use TypoMetrics: {self.os2_use_typometrics}\n"
        output += f"HHEA Ascent: {self.hhea_ascent}\n"
        output += f"HHEA Descent: {self.hhea_descent}\n"
        output += f"HHEA LineGap: {self.hhea_linegap}\n"
        output += "NAMEテーブル\n"
        for name in self.name_records:
            output += str(name)
        return output


@dataclass
class AverageSizeResult:
    count: Optional[int] = None
    avg_w: Optional[float] = None
    avg_h: Optional[float] = None

    def __str__(self):
        output = "[サイズ平均測定結果]\n"
        output += f"平均算出に用いたグリフ数: {self.count}\n"
        output += f"平均値: W:{self.avg_w:.3f}, H:{self.avg_h:.3f}\n"
        return output


@dataclass
class MetricsSetResult:
    font_obj: Optional[TTFont] = None
    old_upm: Optional[int] = None
    new_upm: Optional[int] = None
    need_scale_size: Optional[float] = None

    def __str__(self):
        output = "[メトリクス設定結果]\n"
        output += f"変更前のUPM: {self.old_upm}\n"
        output += f"変更後のUPM: {self.new_upm}\n"
        output += f"必要な拡大率: x{self.need_scale_size}\n"
        return output


@dataclass
class RemoveEmptyResult:
    font_obj: Optional[TTFont] = None
    all_glyphs: Optional[str] = None
    removed_glyphs: Optional[str] = None

    def __str__(self):
        output = "[空白グリフ消去結果]\n"
        output += f"すべてのグリフ: {self.all_glyphs}\n"
        output += f"削除されたグリフ: {self.removed_glyphs}\n"
        return output


@dataclass
class SubsetResult:
    font_obj: Optional[TTFont] = None
    non_existed_glyphs: Optional[str] = None

    def __str__(self):
        output = "[サブセット結果]\n"
        output += f"欠落しているグリフ: {self.non_existed_glyphs}\n"
        return output
