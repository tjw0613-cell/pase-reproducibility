"""Place verified Origin PDFs at their native size, then add editable text/layout.

No data mark, interval, curve or statistical result is drawn here.
Shared layout helpers only. Run compose_2_5_6.py or compose_3_4_s1.py.
"""
from pathlib import Path
from datetime import datetime, timezone
import csv, hashlib, json, math, os
import fitz
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
OUT=Path(os.environ['PASE_FIGURE_OUTPUT_DIR']).resolve(); OUT.mkdir(parents=True, exist_ok=True)
PLANS=ROOT/'plans'; PANELS=ROOT/'panels'
from font_policy import resolve_fonts
FONT_INFO=resolve_fonts()
ARIAL=Path(FONT_INFO['regular'])
ARIAL_BOLD=Path(FONT_INFO['bold'])
MM=72/25.4
BLUE='#0072B2'; VERM='#D55E00'; BLACK='#111111'; GREY='#555555'; RULE='#D7DDE1'
AUTHOR='Jinwei Tang; Yunfan Lin; Linrui Cai; Yali Wen; Guangyang Chen; Li Huang'
SCENARIOS=['global_null','fixed_positive','heterogeneous_positive']
SCENARIO_LABELS=['Null','Fixed effect','Heterogeneous effects']
COHORTS=['GSE234933','GSE181919','GSE310797']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def rgb(s):return tuple(int(s[i:i+2],16)/255 for i in (1,3,5))
def load_csv(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def spec(id):return json.loads((PLANS/(id+'.json')).read_text(encoding='utf-8'))

class Composer:
    def __init__(self,name,height):
        self.name=name;self.doc=fitz.open();self.page=self.doc.new_page(width=180*MM,height=height*MM)
        self.font=fitz.Font(fontfile=str(ARIAL));self.bold=fitz.Font(fontfile=str(ARIAL_BOLD))
        self.page.insert_font(fontname='ArialPASE',fontfile=str(ARIAL))
        self.page.insert_font(fontname='ArialPASEBold',fontfile=str(ARIAL_BOLD))
        self.texts=[];self.placed=[]
    def text(self,x,y,s,size=7.5,bold=False,color=BLACK,align='left',rotate=0):
        font=self.bold if bold else self.font
        w=font.text_length(s,fontsize=size)
        xp=x*MM-(w/2 if align=='center' else w if align=='right' else 0)
        self.page.insert_text((xp,y*MM),s,fontname='ArialPASEBold' if bold else 'ArialPASE',fontsize=size,color=rgb(color),rotate=rotate)
        self.texts.append({'text':s,'font_pt':size,'x_mm':xp/MM,'baseline_y_mm':y,'width_mm':w/MM,'rotate':rotate})
    def line(self,x1,y1,x2,y2,color=RULE,width=.55):
        self.page.draw_line((x1*MM,y1*MM),(x2*MM,y2*MM),color=rgb(color),width=width)
    def panel_title(self,letter,title,x,y):
        self.text(x,y,letter,10,True,color='#000000');self.text(x+5,y,title,8.2,True)
    def symbol(self,x,y,color,kind='circle',r=.65):
        rect=fitz.Rect((x-r)*MM,(y-r)*MM,(x+r)*MM,(y+r)*MM)
        if kind=='circle':self.page.draw_oval(rect,color=rgb(color),fill=rgb(color),width=.5)
        else:self.page.draw_rect(rect,color=rgb(color),fill=rgb(color),width=.5)
    def legend_item(self,x,y,text,color,kind):
        self.line(x,y-.7,x+4,y-.7,color,.75);self.symbol(x+2,y-.7,color,kind)
        self.text(x+6,y,text)
    def place(self,id,x,y):
        s=spec(id);source=PANELS/id/'result.pdf'
        if not source.is_file():raise FileNotFoundError(f'Origin panel is not ready: {source}')
        with fitz.open(source) as part:
            w,h=s['width_mm'],s['height_mm']
            assert len(part)==1
            original_size=[part[0].rect.width,part[0].rect.height]
            # Origin's PDF page rounds up to whole points. Remove only that blank
            # right/bottom canvas sliver; keep the nominal millimetre geometry 1:1.
            assert abs(part[0].rect.width/MM-w)<.36,(id,'width',part[0].rect.width/MM,w)
            assert abs(part[0].rect.height/MM-h)<.36,(id,'height',part[0].rect.height/MM,h)
            clip=fitz.Rect(0,0,w*MM,h*MM)
            self.page.show_pdf_page(fitz.Rect(x*MM,y*MM,(x+w)*MM,(y+h)*MM),part,0,clip=clip)
        self.placed.append({'id':id,'source_pdf_sha256':sha(source),'x_mm':x,'y_mm':y,'width_mm':w,'height_mm':h,'scale':1.0,
                            'original_pdf_size_pt':original_size,'clip_rect_pt':[0,0,w*MM,h*MM],
                            'trimmed_blank_canvas_pt':{'right':original_size[0]-w*MM,'bottom':original_size[1]-h*MM},
                            'source_pdf_modified':False})
        return s
    def y_data(self,s,y,top):
        lo,hi=s['ylim'][:2];box=s['layer_box'];h=s['height_mm']
        return top+h*box[1]/100+h*box[3]/100*(hi-y)/(hi-lo)
    def x_data(self,s,x,left):
        lo,hi=s['xlim'][:2];box=s['layer_box'];w=s['width_mm']
        return left+w*box[0]/100+w*box[2]/100*(x-lo)/(hi-lo)
    def save(self):
        self.doc.set_metadata({'title':self.name.replace('_',' '),'author':AUTHOR,'creator':'PASE authors','subject':'Origin-native data panels with external vector layout'})
        pdf=OUT/(self.name+'.pdf');self.doc.save(pdf,garbage=4,deflate=True)
        with fitz.open(pdf) as d:
            page=d[0]
            page.get_pixmap(dpi=300,alpha=False).save(OUT/(self.name+'.png'))
            pix=page.get_pixmap(dpi=600,alpha=False)
            Image.frombytes('RGB',[pix.width,pix.height],pix.samples).save(OUT/(self.name+'.tiff'),compression='tiff_lzw',dpi=(600,600))
            svg = page.get_svg_image(text_as_path=False)
            # Match the white PDF/raster canvas in SVG viewers as well.
            end = svg.index('>', svg.index('<svg')) + 1
            svg = svg[:end] + '<rect width="100%" height="100%" fill="#ffffff"/>' + svg[end:]
            (OUT/(self.name+'.svg')).write_text(svg,encoding='utf-8')
            page.get_pixmap(matrix=fitz.Matrix(2,2),alpha=False).save(OUT/(self.name+'_PDF_preview.png'))
            check={'native_width_mm':page.rect.width/MM,'native_height_mm':page.rect.height/MM,'embedded_rasters':len(page.get_images()),'body_min_font_pt':min(t['font_pt'] for t in self.texts),'text_outside_page':[]}
            for t in self.texts:
                if t['rotate']:continue
                if t['x_mm']<-.05 or t['x_mm']+t['width_mm']>180.05 or t['baseline_y_mm']>page.rect.height/MM:
                    check['text_outside_page'].append(t)
        assert not check['text_outside_page'],check['text_outside_page']
        receipt={'created_utc':datetime.now(timezone.utc).isoformat(),'figure':self.name,'backend':'Origin data PDFs + PyMuPDF vector composition','data_marks_redrawn':False,'panel_sources':self.placed,'checks':check,'overlay_text':self.texts,'font_policy':FONT_INFO,'visual_QA':'not performed by this command','artifacts':{ext:sha(OUT/(self.name+'.'+ext)) for ext in ['pdf','svg','png','tiff']}}
        (OUT/(self.name+'_composition.json')).write_text(json.dumps(receipt,indent=2,ensure_ascii=False),encoding='utf-8')
        self.doc.close()
        return receipt


def q_label(q):
    if q>=.001:return f'q = {q:.2g}'
    e=math.floor(math.log10(q));sup=str(e).translate(str.maketrans('-0123456789','⁻⁰¹²³⁴⁵⁶⁷⁸⁹'))
    return f'q = {q/10**e:.1f} × 10{sup}'

def draw_q(c,x,y,q):
    # Arial has no guaranteed U+207B glyph: use an editable positioned exponent.
    if q>=.001:
        c.text(x,y,f'q = {q:.2g}')
        return
    exponent=math.floor(math.log10(q))
    base=f'q = {q/10**exponent:.1f} × 10'
    c.text(x,y,base)
    dx=c.font.text_length(base,fontsize=7.5)/MM
    c.text(x+dx+.15,y-1.25,str(exponent).replace('-','−'),7)


