#!/usr/bin/env fontforge
import fontforge
import sys
import os

os.environ["LANG"] = "C"
os.environ["LC_ALL"] = "C"

def extract_font_collection(input_path):
    """OTC及びTTCといったフォントコレクションを抽出する
           input_path: フォントコレクションファイルパス
           return: フォントファイルパスリスト
    """

    # ファイルが存在しない場合
    if not os.path.exists(input_path):
        print(f"エラー: {input_path}が存在しないため処理を終了。")
        return

    # 処理開始
    print(f"--- 抽出開始: {input_path} ---")

    # 抽出して出力
    generated_files = []
    target_dir = os.path.dirname(os.path.abspath(input_path))
    ext = os.path.splitext(input_path)[1].lower()
    default_out_ext = ".ttf" if ext == ".ttc" else ".otf"
    font_names = fontforge.fontsInFile(input_path)
    for name in font_names:
        font = fontforge.open(f"{input_path}({name})")
        safe_name = name.replace(" ", "_").replace("/", "-")
        output_filename = f"{safe_name}{default_out_ext}"
        full_path = os.path.join(target_dir, output_filename)
        print(f"フォントを抽出中:{output_filename:<50}", end="\r")
        font.generate(full_path)
        font.close()
        generated_files.append(full_path)

    # 処理終了
    print(f"--- 抽出完了: {generated_files} ---")

    return generated_files

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用法: fontforge -quiet -script extract_font_collection.py <フォントコレクションファイル>")
        print("例: fontforge -quiet -script convert_otf2ttf.py example.otc")
    else :
        extract_font_collection(sys.argv[1])