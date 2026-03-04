from dataclasses import dataclass
from typing import Optional

from fontTools.ttLib import TTFont


@dataclass
class HarmonizeFontMetricsResult:
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
