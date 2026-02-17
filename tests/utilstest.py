class MockGlyph:
    # 代入時のチェックを避けるため、内部の辞書に直接設定する
    def __init__(self, xmin, xmax, ymin, ymax):
        self.xMin, self.xMax = xmin, xmax
        self.yMin, self.yMax = ymin, ymax

    def expand(self, edit):
        pass  # 念のため追加
