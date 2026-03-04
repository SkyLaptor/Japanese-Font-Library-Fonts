from dataclasses import dataclass, field


@dataclass
class SwfTagInspectionResult:
    path: str
    signature: str
    swf_version: int
    frame_count: int
    has_definefont2: bool
    has_definefont3: bool
    has_definefont4: bool
    tag_counts: dict[int, int] = field(default_factory=dict)

    def __str__(self) -> str:
        lines = [
            "[SWFタグ解析]",
            f"Path: {self.path}",
            f"Signature: {self.signature}",
            f"SWF Version: {self.swf_version}",
            f"Frame Count: {self.frame_count}",
            f"DefineFont2(48): {self.has_definefont2}",
            f"DefineFont3(75): {self.has_definefont3}",
            f"DefineFont4(91): {self.has_definefont4}",
            "Tag Counts:",
        ]
        for tag_id in sorted(self.tag_counts):
            lines.append(f"  tag {tag_id}: {self.tag_counts[tag_id]}")
        return "\n".join(lines) + "\n"
