from dataclasses import dataclass
from typing import Optional


@dataclass
class AverageSizeResult:
    count: Optional[int] = None
    avg_w: Optional[float] = None
    avg_h: Optional[float] = None
    count_latin: Optional[int] = None
    avg_w_latin: Optional[float] = None
    avg_h_latin: Optional[float] = None

    def __str__(self):
        avg_w = 0.0 if self.avg_w is None else self.avg_w
        avg_h = 0.0 if self.avg_h is None else self.avg_h
        avg_w_latin = 0.0 if self.avg_w_latin is None else self.avg_w_latin
        avg_h_latin = 0.0 if self.avg_h_latin is None else self.avg_h_latin

        output = "[サイズ平均測定結果]\n"
        output += f"平均算出に用いたグリフ数(CJK): {self.count}\n"
        output += f"平均値(CJK): 横幅:{avg_w:.1f}, 縦幅:{avg_h:.1f}\n"
        output += f"平均算出に用いたグリフ数(Latin): {self.count_latin}\n"
        output += f"平均値(Latin): 横幅:{avg_w_latin:.1f}, 縦幅:{avg_h_latin:.1f}\n"
        return output
