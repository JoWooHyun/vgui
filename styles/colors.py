"""
VERICOM DLP 3D Printer GUI - Color Constants
Design System: Dynamic Theme Support (Light/Dark/High Contrast)
"""


class _ColorsMeta(type):
    """Colors 클래스의 메타클래스 - 동적 속성 접근"""

    # 현재 테마 색상 (기본값: Light)
    _current = {
        # Primary
        "NAVY": "#1E3A5F",
        "NAVY_LIGHT": "#2D4A6F",
        "NAVY_DARK": "#152C4A",
        "CYAN": "#06B6D4",
        "CYAN_LIGHT": "#22D3EE",
        "CYAN_DARK": "#0891B2",
        # Semantic
        "RED": "#DC2626",
        "RED_LIGHT": "#FEE2E2",
        "RED_DARK": "#B91C1C",
        "TEAL": "#14B8A6",
        "TEAL_LIGHT": "#CCFBF1",
        "AMBER": "#F59E0B",
        "AMBER_LIGHT": "#FEF3C7",
        "GREEN": "#22C55E",
        "GREEN_LIGHT": "#DCFCE7",
        # Neutral
        "WHITE": "#FFFFFF",
        "BG_PRIMARY": "#FFFFFF",
        "BG_SECONDARY": "#F8FAFC",
        "BG_TERTIARY": "#F1F5F9",
        "BORDER": "#E2E8F0",
        "BORDER_LIGHT": "#F1F5F9",
        "TEXT_PRIMARY": "#334155",
        "TEXT_SECONDARY": "#64748B",
        "TEXT_DISABLED": "#94A3B8",
        "TEXT_EMPHASIS": "#0F172A",
    }

    def __getattr__(cls, name):
        """동적 속성 접근"""
        if name.startswith('_'):
            raise AttributeError(name)
        if name in cls._current:
            return cls._current[name]
        # 특수 속성
        if name == "NAVY_ALPHA_10":
            return cls.with_alpha(cls._current["NAVY"], 0.1)
        if name == "CYAN_ALPHA_10":
            return cls.with_alpha(cls._current["CYAN"], 0.1)
        if name == "CYAN_ALPHA_20":
            return cls.with_alpha(cls._current["CYAN"], 0.2)
        raise AttributeError(f"'{cls.__name__}' has no attribute '{name}'")


class Colors(metaclass=_ColorsMeta):
    """동적 컬러 팔레트 - ThemeManager와 연동"""

    @classmethod
    def with_alpha(cls, hex_color: str, alpha: float) -> str:
        """HEX 컬러를 RGBA로 변환"""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f"rgba({r}, {g}, {b}, {alpha})"

    @classmethod
    def apply_theme(cls, theme_colors: dict):
        """테마 색상 적용"""
        for key, value in theme_colors.items():
            if key in _ColorsMeta._current and key != "name":
                _ColorsMeta._current[key] = value

    @classmethod
    def get(cls, name: str) -> str:
        """색상 이름으로 값 가져오기"""
        return _ColorsMeta._current.get(name, "#000000")

    @classmethod
    def get_current_theme_colors(cls) -> dict:
        """현재 테마 색상 전체 반환"""
        return _ColorsMeta._current.copy()
