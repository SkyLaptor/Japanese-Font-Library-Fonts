from dataclasses import dataclass
from typing import Optional

from fontTools.ttLib import TTFont


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


@dataclass
class HarmonizeResult:
    font_obj: Optional[TTFont] = None
    is_upm_change: Optional[bool] = None
    final_scale_width: Optional[float] = None
    final_scale_height: Optional[float] = None

    def __str__(self):
        output = "[フォントメトリクス更新結果]\n"
        output += f"UPMの変更: {self.is_upm_change}\n"
        output += f"最終的な横倍率: x{self.final_scale_width}\n"
        output += f"最終的な縦倍率: x{self.final_scale_height}\n"
        return output
