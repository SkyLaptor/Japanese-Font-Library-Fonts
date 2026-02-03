chars = set()

ranges = [
    (0x0020, 0x007E), # Basic Latin
    (0x00A0, 0x00FF), # Latin-1 Supplement
    (0x0100, 0x017F), # Latin Extended-A (欧州広域)
    (0x0400, 0x04FF), # Cyrillic (キリル文字)
    (0x2000, 0x206F), # General Punctuation (一般的な句読点)
    (0x20A0, 0x20CF), # Currency Symbols (通貨記号)
    (0x2100, 0x214F), # Letterlike Symbols (単位記号など)
    (0x2150, 0x218F), # Number Forms (ローマ数字など)
    (0x2190, 0x21FF), # Arrows (矢印)
    (0x2200, 0x22FF), # Mathematical Operators (数学記号)
    (0x2460, 0x24FF), # Enclosed Alphanumerics (丸囲み文字)
    (0x2500, 0x257F), # Box Drawing (罫線)
    (0x25A0, 0x25FF), # Geometric Shapes (四角・三角・星など)
    (0x2600, 0x26FF), # Miscellaneous Symbols (天気・チェス・トランプなど)
    (0x3000, 0x303F), # CJK Symbols and Punctuation (全角句読点)
    (0x3040, 0x309F), # Hiragana
    (0x30A0, 0x30FF), # Katakana
    (0x3400, 0x4DBF), # CJK Unified Ideographs Extension A (第3・4水準)
    (0x4E00, 0x9FFF), # CJK Unified Ideographs (第1～4水準中心)
    (0xFF00, 0xFFEF), # Halfwidth and Fullwidth Forms (全角英数・半角カナ)
]

for start, end in ranges:
    for i in range(start, end + 1):
        chars.add(chr(i))

with open('subset.txt', 'w', encoding='utf-8') as f:
    f.write(''.join(sorted(list(chars))))