from dataclasses import dataclass, field
from typing import Optional


@dataclass
class NameRecord:
    name_id: Optional[int] = None
    label: Optional[str] = None
    value: Optional[str] = None

    def __str__(self):
        output = f"[NAMEレコード] {self.name_id}, {self.label}, {self.value}\n"
        return output


@dataclass
class FontInfoResult:
    is_ttf: Optional[bool] = None
    is_cff: Optional[bool] = None
    is_cff2: Optional[bool] = None
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
    post_underline_position: Optional[int] = None
    post_underline_thickness: Optional[int] = None
    opentype_feature_count: Optional[int] = None
    name_records: list[NameRecord] = field(default_factory=list)

    def __str__(self):
        output = "[フォント情報]\n"
        output += f"TrueType: {self.is_ttf}\n"
        output += f"PostScript (CFF): {self.is_cff}\n"
        output += f"PostScript (CFF2 / Variable): {self.is_cff2}\n"
        output += f"作成日時: {self.created_time}\n"
        output += f"更新日時: {self.modified_time}\n"
        output += f"総グリフ数: {self.glyph_count_all}\n"
        output += f"グリフ数(Unicode割当済): {self.glyph_count_uni}\n"
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
        output += f"POST Underline Position: {self.post_underline_position}\n"
        output += f"POST Underline Thickness: {self.post_underline_thickness}\n"
        output += f"OpenType機能数: {self.opentype_feature_count}\n"
        output += "NAMEテーブル\n"
        for name in self.name_records:
            output += str(name)
        return output
