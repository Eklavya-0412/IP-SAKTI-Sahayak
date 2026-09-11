"""Render the project report as an accessible, paginated submission PDF."""
import re
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,KeepTogether,Flowable
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'deliverables';OUT.mkdir(exist_ok=True)
font=Path('C:/Windows/Fonts/segoeui.ttf')
if font.exists():
    pdfmetrics.registerFont(TTFont('Report',str(font)));pdfmetrics.registerFont(TTFont('ReportBold','C:/Windows/Fonts/segoeuib.ttf'));pdfmetrics.registerFontFamily('Report',normal='Report',bold='ReportBold',italic='Report',boldItalic='ReportBold')
    family='Report'
else:family='Helvetica'
green=colors.HexColor('#234335');saffron=colors.HexColor('#B87730');cream=colors.HexColor('#F5F3EC')
styles=getSampleStyleSheet()
for style in styles.byName.values():style.fontName=family
styles['Normal'].fontSize=9;styles['Normal'].leading=13;styles['Normal'].spaceAfter=6
styles['Title'].fontSize=32;styles['Title'].leading=38;styles['Title'].textColor=green
for name,size in [('Heading1',23),('Heading2',15),('Heading3',11)]:
    styles[name].fontSize=size;styles[name].leading=size*1.25;styles[name].textColor=green;styles[name].spaceBefore=12;styles[name].spaceAfter=8
styles.add(ParagraphStyle('Cell',fontName=family,fontSize=7.4,leading=10,spaceAfter=1))
styles.add(ParagraphStyle('CodeBlock',fontName='Courier',fontSize=7,leading=10,backColor=cream,borderPadding=8,spaceAfter=10))
def markup(value):
    value=escape(value)
    value=re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)',r'<link href="\2" color="#234335">\1</link>',value)
    value=re.sub(r'\*\*([^*]+)\*\*',r'<b>\1</b>',value)
    value=re.sub(r'`([^`]+)`',r'<font face="Courier">\1</font>',value)
    return value
class Diagram(Flowable):
    def __init__(self,kind):super().__init__();self.kind=kind;self.width=475;self.height=150
    def draw(self):
        c=self.canv
        labels={'flow':['React workspace','API scope / consent','Retrieval + graph','Verify / excerpts','Source snapshots','PostgreSQL','Gemini / Ollama','Optional Bhashini'],
                'data':['User / session','Owned case','Private documents','Review submission','Source','Source version','Evidence chunk','Graph / answer trace'],
                'deploy':['TLS (production)','Nginx web','FastAPI','PostgreSQL','Migration job','Worker','Document volume','Database volume']}[self.kind]
        for i,label in enumerate(labels):
            x=(i%4)*119;y=88-(i//4)*72
            c.setFillColor(cream);c.setStrokeColor(green);c.roundRect(x,y,109,42,4,stroke=1,fill=1)
            c.setFillColor(green);c.setFont(family,8);c.drawCentredString(x+54.5,y+18,label)
            if i%4<3:c.line(x+110,y+21,x+119,y+21)
        c.setFillColor(saffron);c.setFont(family,8);c.drawString(0,0,'Separate trust boundaries; see the editable Mermaid diagrams in ARCHITECTURE.md.')
text=(ROOT/'docs/PROJECT_REPORT.md').read_text(encoding='utf-8');lines=text.splitlines();story=[];i=0;h1=0
while i<len(lines):
    line=lines[i].strip();i+=1
    if not line:continue
    if line=='---':continue
    if line.startswith('```'):
        code=[];language=line[3:]
        while i<len(lines) and not lines[i].strip().startswith('```'):code.append(lines[i]);i+=1
        i+=1
        if language=='mermaid':story.append(Diagram('data' if 'erDiagram' in '\n'.join(code) else 'deploy' if 'flowchart TB' in '\n'.join(code) else 'flow'))
        else:
            for row in code:
                for start in range(0,max(1,len(row)),100):story.append(Paragraph(escape(row[start:start+100]).replace(' ','&#160;'),styles['CodeBlock']))
        continue
    if line.startswith('|'):
        rows=[line]
        while i<len(lines) and lines[i].strip().startswith('|'):rows.append(lines[i].strip());i+=1
        cells=[[Paragraph(markup(c.strip()),styles['Cell']) for c in row.strip('|').split('|')] for row in rows if not re.match(r'^\|[\s:|\-]+\|$',row)]
        widths=[475/len(cells[0])]*len(cells[0]);table=Table(cells,colWidths=widths,repeatRows=1,hAlign='LEFT')
        table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),cream),('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),.3,colors.HexColor('#D9DDD5')),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3)]));story.extend([table,Spacer(1,12)]);continue
    if line.startswith('# '):
        h1+=1
        if h1>1:story.append(PageBreak())
        story.append(Paragraph(markup(line[2:]),styles['Title'] if h1==1 else styles['Heading1']));continue
    if line.startswith('## '):story.append(Paragraph(markup(line[3:]),styles['Heading2']));continue
    if line.startswith('### '):story.append(Paragraph(markup(line[4:]),styles['Heading3']));continue
    if line.startswith('- '):line='• '+line[2:]
    story.append(Paragraph(markup(line),styles['Normal']))
def footer(c,doc):
    c.saveState();c.setStrokeColor(colors.HexColor('#DBDED5'));c.line(60,42,535,42);c.setFillColor(green);c.setFont(family,8)
    c.drawString(60,29,'IP-SAKTI Sahayak · Deployable pilot · Information, not legal advice');c.drawRightString(535,29,str(doc.page));c.restoreState()
target=OUT/'IP-SAKTI-Project-Report.pdf'
SimpleDocTemplate(str(target),pagesize=(595.28,841.89),rightMargin=60,leftMargin=60,topMargin=55,bottomMargin=60,title='IP-SAKTI Sahayak — Project Report',author='IP-SAKTI Project').build(story,onFirstPage=footer,onLaterPages=footer)
print(target)
