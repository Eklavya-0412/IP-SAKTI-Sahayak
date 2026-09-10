"""Unicode fonts for case exports; no remote font download at request time."""
from pathlib import Path
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def configure_case_styles(styles):
    candidates=[Path('/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf'),Path('C:/Windows/Fonts/Nirmala.ttc')]
    for path in candidates:
        if path.exists():
            if 'CaseUnicode' not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont('CaseUnicode',str(path),subfontIndex=0,shapable=True))
                pdfmetrics.registerFontFamily('CaseUnicode',normal='CaseUnicode',bold='CaseUnicode',italic='CaseUnicode',boldItalic='CaseUnicode')
            for style in styles.byName.values():style.fontName='CaseUnicode';style.shaping=True
            break
    return styles
