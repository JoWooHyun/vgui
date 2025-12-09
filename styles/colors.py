"""
VERICOM DLP 3D Printer GUI - Color Constants
Design System: Navy + Cyan Theme
"""


class Colors:
    """컬러 팔레트 정의"""
    
    # ========== Primary Colors ==========
    NAVY = "#1E3A5F"
    NAVY_LIGHT = "#2D4A6F"
    NAVY_DARK = "#152C4A"
    
    CYAN = "#06B6D4"
    CYAN_LIGHT = "#22D3EE"
    CYAN_DARK = "#0891B2"
    
    # ========== Semantic Colors ==========
    RED = "#DC2626"
    RED_LIGHT = "#FEE2E2"
    RED_DARK = "#B91C1C"
    
    TEAL = "#14B8A6"
    TEAL_LIGHT = "#CCFBF1"
    
    AMBER = "#F59E0B"
    AMBER_LIGHT = "#FEF3C7"
    
    GREEN = "#22C55E"
    GREEN_LIGHT = "#DCFCE7"
    
    # ========== Neutral Colors ==========
    WHITE = "#FFFFFF"
    
    BG_PRIMARY = "#FFFFFF"      # 주 배경
    BG_SECONDARY = "#F8FAFC"    # 카드, 버튼 배경
    BG_TERTIARY = "#F1F5F9"     # 비활성 배경
    
    BORDER = "#E2E8F0"          # 테두리
    BORDER_LIGHT = "#F1F5F9"
    
    TEXT_PRIMARY = "#334155"    # 주요 텍스트
    TEXT_SECONDARY = "#64748B"  # 보조 텍스트
    TEXT_DISABLED = "#94A3B8"   # 비활성 텍스트
    TEXT_EMPHASIS = "#0F172A"   # 강조 텍스트
    
    # ========== Transparent ==========
    NAVY_ALPHA_10 = "rgba(30, 58, 95, 0.1)"
    CYAN_ALPHA_10 = "rgba(6, 182, 212, 0.1)"
    CYAN_ALPHA_20 = "rgba(6, 182, 212, 0.2)"
    
    @classmethod
    def with_alpha(cls, hex_color: str, alpha: float) -> str:
        """HEX 컬러를 RGBA로 변환"""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f"rgba({r}, {g}, {b}, {alpha})"
