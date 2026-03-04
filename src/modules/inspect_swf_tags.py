# Dependencies: FFDec=False, FontForge=False
import struct
import zlib
from pathlib import Path

from const import ENCODE
from models.swf_tag_inspection_result import SwfTagInspectionResult
from utils.file_io import save_text

Result = SwfTagInspectionResult


def _decompress_swf(raw_data: bytes) -> tuple[str, bytes]:
    signature = raw_data[:3]
    if signature == b"FWS":
        return "FWS", raw_data
    if signature == b"CWS":
        return "CWS", raw_data[:8] + zlib.decompress(raw_data[8:])

    sig_str = signature.decode(ENCODE, errors="ignore")
    raise ValueError(f"未対応のSWFシグネチャです: {sig_str}")


def _get_swf_tag_start(data: bytes) -> int:
    bit_pos = 8 * 8
    first_rect_byte = data[8]
    nbits = first_rect_byte >> 3
    rect_bits = 5 + nbits * 4
    bit_pos += rect_bits

    if bit_pos % 8:
        bit_pos += 8 - (bit_pos % 8)

    rect_end_pos = bit_pos // 8
    return rect_end_pos + 4


def inspect_swf_tags(swf_path: Path) -> SwfTagInspectionResult:
    raw_data = swf_path.read_bytes()
    signature, data = _decompress_swf(raw_data)

    swf_version = data[3]
    pos = _get_swf_tag_start(data)

    if pos > len(data):
        raise ValueError("SWFヘッダーの解析に失敗しました。")

    frame_count = struct.unpack("<H", data[pos - 2 : pos])[0]
    tag_counts = {}

    while pos + 2 <= len(data):
        tag_header = struct.unpack("<H", data[pos : pos + 2])[0]
        pos += 2

        tag_type = tag_header >> 6
        tag_len = tag_header & 0x3F
        if tag_len == 0x3F:
            if pos + 4 > len(data):
                break
            tag_len = struct.unpack("<I", data[pos : pos + 4])[0]
            pos += 4

        tag_counts[tag_type] = tag_counts.get(tag_type, 0) + 1

        if tag_type == 0:
            break

        pos += tag_len

    return SwfTagInspectionResult(
        path=str(swf_path),
        signature=signature,
        swf_version=swf_version,
        frame_count=frame_count,
        has_definefont2=48 in tag_counts,
        has_definefont3=75 in tag_counts,
        has_definefont4=91 in tag_counts,
        tag_counts=tag_counts,
    )


def action_inspect_swf_tags(
    input_path: str,
    output_path: str = None,
    debug: bool = False,
    **_,
) -> None:
    swf_path = Path(input_path)
    if not swf_path.exists():
        raise FileNotFoundError(f"ファイルが見つかりません: {input_path}")

    result = inspect_swf_tags(swf_path)
    print(result)

    if output_path is not None:
        saved_path = save_text(
            str(result),
            input_path=input_path,
            output_path=output_path,
            suffix="_swf_tags",
            ext="txt",
        )
        print(f"SWFタグ情報を保存しました: {saved_path}")
