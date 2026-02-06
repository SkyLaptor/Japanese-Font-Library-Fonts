#!/usr/bin/env fontforge
import fontforge
import sys
import os

os.environ["LANG"] = "C"
os.environ["LC_ALL"] = "C"

def main(base_font_path, sub_font_path, output_path=None):
    """フォントを結合して新たなフォントとして出力する
           基本フォントファイルに存在しないグリフが補間される。
           base_font_path: 基本フォントファイルパス
           sub_font_path: 補間フォントファイルパス
           output_path: 出力フォントファイルパス
           return: output_path
    """
    print("=== フォント結合機能を開始 ===")

    # 基本フォントファイルが存在しない場合
    if not os.path.exists(base_font_path):
        print(f"エラー: 基本フォントファイル {base_font_path} が存在しないため処理を終了。")
        return None

    # 補間フォントファイルが存在しない場合
    if not os.path.exists(sub_font_path):
        print(f"エラー: 補間フォントファイル {sub_font_path} が存在しないため処理を終了。")
        return None

    # フォントのオープン
    print("フォントファイルをオープン中...")
    base_font = fontforge.open(base_font_path,("fstypepermitted",))
    sub_font = fontforge.open(sub_font_path,("fstypepermitted",))

    # EMサイズチェック
    if base_font.em != sub_font.em:
        print(f"エラー: フォントファイル同士のEMサイズが不一致。基本:{base_font.em},補間:{sub_font.em} 処理を終了。")
        print("フォントファイルをクローズ中...")
        base_font.close()
        sub_font.close()
        return None

    # フォントの結合
    print("フォントファイルの結合中...")
    base_font.mergeFonts(sub_font_path)

    # フォントの出力
    print("結合済みフォントを出力中...")
    if not output_path:
        print("出力先が未指定のため、基本フォントと同じ場所に出力。")
        directory = os.path.dirname(base_font_path) or "."
        base_name = os.path.splitext(os.path.basename(base_font_path))[0]
        output_file = f"{base_name}_merged"
        output_path = os.path.join(directory, output_file+".ttf")
    base_font.generate(output_path)

    # フォントのクローズ
    print("フォントファイルをクローズ中...")
    base_font.close()
    sub_font.close()

    print("=== フォント結合機能を終了 ===")
    return output_path


if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) < 2:
        print("使用方法: fontforge -quiet -script merge_font.py <基本フォントファイルパス> <補間フォントファイルパス> [出力フォントファイルパス]")
    else:
        main(*args)