from pathlib import Path
import json, math, textwrap, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from new15_article_data import ARTICLES

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent if HERE.name == 'scripts' else HERE
INPUT=ROOT/'editorial_sources_new15'
OUT=ROOT/'assets'
OUT.mkdir(exist_ok=True,parents=True)
IMGHOST='https://cozyloops.site/assets/'
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
SERIF='/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf'
FONTS={n:ImageFont.truetype(path,n) for n,path in [(38,SERIF),(29,BOLD),(25,FONT),(21,FONT),(20,BOLD),(18,FONT),(55,SERIF)]}

# Source photos are original AI-generated editorial visuals. Grid crops are illustrative, not actual crochet samples.
MAP={
'bookmarks':[('bookmarks',3,3,0,0,1),('bookmarks',3,3,2,2,1),('bookmarks',3,3,1,2,1),('bookmarks',3,3,1,1,1)],
'phone':[('coverA',5,3,3,1,.61),('coverD',4,2,3,1,.62)],
'coasters':[('coverA',5,3,0,2,.65),('coverC',5,3,0,1,.62)],
'tulips':[('coverA',5,3,3,0,.64),('coverC',5,3,0,2,.60)],
'butterfly':[('coverA',5,3,2,0,.65),('coverD',4,2,2,0,.63)],
'axolotl':[('coverA',5,3,1,0,.64),('coverD',4,2,2,1,.63)],
'penguin':[('coverB',5,3,3,2,.63)],
'dinosaur':[('coverB',5,3,4,2,.64)],
'strawberry':[('coverD',4,2,1,1,.65)],
'bow':[('coverC',5,3,3,1,.64)],
'booties':[('coverA',5,3,0,1,.65)],
'hats':[('coverA',5,3,1,1,.63),('coverC',5,3,2,2,.62)],
'flowerkeys':[('coverE',5,3,4,2,.64)],
'woodland':[('coverA',5,3,3,2,.64)],
'farm':[('coverA',5,3,2,2,.64)],
}

COLORS=[('#F9F2ED','#7B574C','#DCA9A7'),('#F4F2E9','#365E52','#C5D6C0'),('#FBF4EA','#7F526C','#DFC6D4'),('#FFF4EA','#8D653B','#E7C2A0'),('#EEF6F5','#315C69','#AECCD4')]
ART={i:Image.open(INPUT/f'{i}.webp').convert('RGB') for i in ('coverA','coverB','coverC','coverD','coverE','bookmarks')}

def rgb(h): return tuple(int(h[i:i+2],16) for i in (1,3,5))
def rect(draw,xy,r,fill,outline=None,width=1):draw.rounded_rectangle(xy,radius=r,fill=fill,outline=outline,width=width)
def photo(item,index):
    src,cols,rows,c,r,frac = item
    image=ART[src]
    # Crop product photography only, excluding synthetic title and badge regions
    # from the original editorial contact sheets.
    if src=='coverA':
        y1=int(image.height*r/rows + image.height/rows*.54)
        y2=int(image.height*(r+1)/rows - 5)
    elif src=='coverD':
        y1=int(image.height*r/rows + image.height/rows*.40)
        y2=int(image.height*(r+1)/rows - 8)
    elif src=='coverB':
        y1=int(image.height*r/rows+28)
        y2=int(image.height*r/rows+image.height/rows*.57)
    elif src=='coverC':
        starts=[102,431,742]
        ends=[293,611,913]
        y1,y2=starts[r],ends[r]
    elif src=='coverE':
        starts=[9,355,681]
        ends=[230,556,860]
        y1,y2=starts[r],ends[r]
    else:
        y1=int(image.height*r/rows+7)
        y2=int(image.height*(r+1)/rows-7)
    x1=int(image.width*c/cols)+10
    x2=int(image.width*(c+1)/cols)-10
    im=image.crop((x1,y1,x2,y2)); return ImageEnhance.Contrast(im).enhance(1.02)

def fit(im,w,h):
    r=max(w/im.width,h/im.height);new=im.resize((int(im.width*r)+2,int(im.height*r)+2),Image.Resampling.LANCZOS)
    x=(new.width-w)//2;y=(new.height-h)//2
    return new.crop((x,y,x+w,y+h))

def paragraph(draw,text,x,y,maxw,font,fill,spacing=8,max_lines=7):
    words=text.split();lines=[];cur=''
    for w in words:
        trial=(cur+' '+w).strip()
        if draw.textbbox((0,0),trial,font=font)[2] <= maxw:cur=trial
        else:
            if cur:lines.append(cur)
            cur=w
    if cur:lines.append(cur)
    for line in lines[:max_lines]:draw.text((x,y),line,font=font,fill=fill);y+=font.size+spacing
    return y

def make(slug,seq,topic,ph,idx,sections):
    light,dark,accent=COLORS[idx%len(COLORS)]; bg=rgb(light);ink=rgb(dark);wash=rgb(accent)
    width,height=1200,750
    im=Image.new('RGB',(width,height),bg);d=ImageDraw.Draw(im)
    for y in range(0,height,18):
        shade=tuple(min(255,int(c+1.5*math.sin(y/38))) for c in bg)
        d.line((0,y,width,y),fill=shade,width=1)
    # delicate lines on linen
    d.ellipse((width-250,-175,width+120,195),outline=wash,width=4)
    d.ellipse((-160,height-180,170,height+150),outline=wash,width=3)
    imgs=[photo(x,idx) for x in MAP[ph]]
    pic=fit(imgs[(seq+idx)%len(imgs)],725,655)
    if seq==0:
        # editorial hero: featured photo and softly overlaid copy, no misleading step diagrams
        blurred=fit(imgs[0],width,height).filter(ImageFilter.GaussianBlur(30))
        im.paste(Image.blend(Image.new('RGB',(width,height),bg),blurred,.25),(0,0));d=ImageDraw.Draw(im)
        im.paste(pic,(42,47))
        d.rounded_rectangle((765,47,1154,701),24,fill=(255,253,249))
        d.text((808,94),'CozyLoops  •  FREE CROCHET',font=FONTS[20],fill=ink)
        paragraph(d,topic,805,165,312,FONTS[38],ink,spacing=10,max_lines=7)
        d.line((808,448,1099,448),fill=wash,width=4)
        paragraph(d,'Original, practical crochet notes with stitch counts and finishing guidance.',808,480,305,FONTS[21],ink,9,7)
        d.text((807,648),'EDITORIAL IMAGE  •  AI VISUAL',font=FONTS[18],fill=ink)
    else:
        im.paste(pic,(32,47));d=ImageDraw.Draw(im)
        rect(d,(779,48,1168,700),26,(255,253,249))
        d.text((815,86),'CozyLoops  /  PHOTO GUIDE',font=FONTS[18],fill=ink)
        labels=['','TOOLS & YARN','STITCH BASICS','START THE PROJECT','BUILD THE SHAPE','ASSEMBLE & FINISH','CHECK YOUR SIZE','FIX COMMON MISTAKES','STYLE YOUR PROJECT']
        d.text((810,148),labels[seq],font=FONTS[29],fill=ink)
        d.line((811,198,1120,198),fill=wash,width=4)
        body=sections[seq-1]
        paragraph(d,body,810,244,306,FONTS[21],ink,spacing=11,max_lines=12)
        d.text((811,640),'VISUAL REFERENCE  ·  NOT TESTED',font=FONTS[18],fill=ink)
    im.save(OUT/f'{slug}-{seq+1:02d}.webp','WEBP',quality=88,method=5)

INTRO='''**Editorial note:** This article features original instructions and AI-generated editorial project visuals. The illustrations are not photographs of physically crocheted samples; stitch counts and construction logic have been reviewed, but no finished sample has been independently wear-tested or safety-certified. Use the written directions—not visual stitch shapes—as your guide. All stitch names use **US crochet terms** unless stated otherwise.'''
CYC='[Craft Yarn Council crochet abbreviations](https://craftyarncouncil.com/node/31)'
related={
 'bookmarks':'crochet-flower-coasters-free-pattern', 'phone':'crochet-strawberry-crossbody-bag-guide',
 'coasters':'crochet-daisy-flower-bookmark-free-pattern','tulips':'crochet-flower-keychains-scrap-yarn-guide',
 'butterfly':'pink-axolotl-crochet-amigurumi-guide','axolotl':'crochet-penguin-ornament-free-pattern',
 'penguin':'mini-crochet-dinosaur-amigurumi-guide','dinosaur':'mini-woodland-amigurumi-animal-ideas',
 'strawberry':'crochet-phone-pouch-crossbody-size-guide','bow':'crochet-flower-keychains-scrap-yarn-guide',
 'booties':'crochet-baby-animal-hats-bear-bunny-frog-guide','hats':'crochet-baby-booties-sizing-sole-guide',
 'flowerkeys':'crochet-daisy-flower-bookmark-free-pattern','woodland':'mini-farm-animals-amigurumi-collection',
 'farm':'mini-woodland-amigurumi-animal-ideas'
}

def article(a, idx):
    slug=a['slug'];p=a['photo'];full_title=a['title']
    content=[]
    def add(x):content.append(x)
    def fig(j,alt):add(f'![{alt}]({IMGHOST}{slug}-{j:02d}.webp)')
    add(a['overview'])
    add(INTRO)
    add(f'## Quick Project Overview')
    add(f'**What you will learn:** {a["excerpt"]} **Skill level:** Beginner to confident beginner depending on shaping and assembly. **Terminology:** US. **Size:** Make a gauge swatch; finished size depends on yarn, hook and tension.')
    add('Think of this as a small, useful project rather than a decorative photograph. Read the whole pattern before you cut yarn, then identify the edges, openings and pieces to sew before starting.')
    add('## Materials and Tools')
    fig(2,f'Styled editorial visual showing materials for {a["keyword"]}')
    add(a['materials'])
    add('For a reliable result, choose smooth yarn with visible stitches, the hook recommended by your yarn or pattern notes, a tapestry needle for secure finishing, and a stitch marker for shaping rounds. Avoid changing yarn weight halfway through the project: dimensions and texture can shift noticeably.')
    add('## Crochet Abbreviations and a Practice Swatch')
    fig(3,f'Crochet stitch closeup and reference panel for {a["keyword"]}')
    add('- **ch:** chain; **sc:** single crochet; **hdc:** half double crochet; **dc:** double crochet; **tr:** treble crochet.')
    add('- **sl st:** slip stitch; **inc:** two stitches worked into one; **dec:** decrease; **MR:** magic ring; **BLO:** back loop only.')
    add('- **[number]:** number of stitches expected after completing a row or round. A turning chain counts only when the instructions explicitly say so.')
    add(f'For standardized terms see the {CYC}. Before shaping a project, make a small swatch and count ten consecutive stitches. Compare your tension with any measurements stated below instead of assuming every crocheter produces the same size.')
    add('## Free Pattern or Construction Tutorial: Step by Step')
    fig(4,f'First construction stage concept for {a["keyword"]}')
    add(a['stitches'])
    add('Take a moment to stop at the end of each numbered row or round, count the top V-shaped stitches, and move your marker. It is faster to correct one row now than unravel several rows later.')
    add('## How to Shape and Assemble It Neatly')
    fig(5,f'Styled visual of shaping techniques for {a["keyword"]}')
    add('Lay the finished pieces on a flat work surface before you sew. Match the front and back, identify a center point, and secure the most visible details only after you are satisfied with alignment. Sew through more than one small stitch when attaching parts that will be handled or moved.')
    add(a['tip1'])
    add('## Finishing and Durability Checklist')
    fig(6,f'Closeup and finishing guide for {a["keyword"]}')
    add(a['tip2'])
    add('Before using or gifting the project, weave tails deeply into matching-color stitches, trim only after confirming the finish is secure, and inspect for uneven tension, protruding knots or fraying. Wash or block only as permitted by the yarn label. Do not claim a design is child-safe or load-bearing without the relevant testing.')
    add('## Sizing and Customization')
    fig(7,f'Sizing and customization visual reference for {a["keyword"]}')
    add(a['fit'])
    add('The most repeatable way to customize a crochet pattern is to change **one variable at a time**: yarn thickness, hook size, or the number of rows and rounds. Record any change and make a sample rather than promising a universal finished size.')
    add('## Troubleshooting: Avoid These Mistakes')
    fig(8,f'Troubleshooting reference visual for {a["keyword"]}')
    add(a['problem'])
    add('- **Unexpected stitch count:** Check whether a turning chain was counted as a stitch. Mark the first stitch in rounds.')
    add('- **Loose finishing:** Pass the yarn needle through several fabric sections before clipping the tail.')
    add('- **Project looks different from the photograph:** Yarn texture, hook size, tension and finishing all affect the result; AI visuals are styling references, not proof of exact construction.')
    add('## Styling, Gift Ideas and Next Projects')
    fig(9,f'Finished styling and handmade gift display of {a["keyword"]}')
    add('Make one complete sample before preparing a matching set. Arrange finished items in coordinated colors and photograph them in natural light with the true scale visible. For a product listing, use photographs of your own finished sample—not AI concept images.')
    add(f'Try the related [CozyLoops tutorial]({"https://cozyloops.site/posts/"+related[p]+"/"}) for a complementary small project, or use our [beginner pattern-reading guide](https://cozyloops.site/posts/crochet-patterns-for-beginners-guide/) to practice abbreviations.')
    add('## Frequently Asked Questions')
    for q,ans in a['faq']:add(f'### {q}\n\n{ans}')
    add('### Can I sell the finished project?\n\nYou may use the instructions as a starting point for making your own work, but verify measurements, construction, durability and applicable product safety requirements before selling. Photograph the exact product you made, especially if you advertise the design or its size.')
    add('### Why do the photos not match every stitch?\n\nAll project images are AI-generated editorial visuals, not documentary step-by-step photos of a tested sample. The written stitch counts and assembly notes are the intended reference. If a technique or measurement is unclear, make a small swatch before continuing.')
    add('## Final Notes')
    add('The most important part of learning crochet is producing something you can inspect and improve. Try the first version slowly, count each row, keep notes on your yarn and hook, and adapt the next version using what you learned. If the project will be handled by children, conduct appropriate safety assessment rather than assuming a handmade item is automatically safe.')
    add('**References and disclosure:** Original CozyLoops editorial instructions; terminology checked against the Craft Yarn Council. Photographs and illustrated references are AI-generated; no independent physical pattern testing has been carried out.')
    return '\n\n'.join(content)

records=[]
for idx,a in enumerate(ARTICLES):
    slug=a['slug'];ph=a['photo']
    stages=[
        a['materials'],
        'Practice the stitches on a small swatch. Count every round and mark the first stitch whenever you work in a spiral.',
        'Begin with the foundation chain or magic ring in the written instructions. Follow each count before moving to the next round.',
        'Continue the shaping exactly as described in the tutorial. Compare both sides before any sewing or closing.',
        'Arrange the parts and sew through several stitches; hide tails and inspect the finish before use.',
        a['fit'],a['problem'],a['tip1']
    ]
    for n in range(9):make(slug,n,a['keyword'].title(),ph,idx,stages)
    content=article(a,idx)
    records.append({
        'title':a['title'],'slug':slug,'excerpt':a['excerpt'],'category':a['category'],'status':'published',
        'image_url':f'{IMGHOST}{slug}-01.webp','image_alt':f'AI-generated editorial cover of {a["keyword"]}',
        'created_at':f'2026-11-07T01:{idx:02d}:00Z','updated_at':'2026-11-07T01:21:00Z','content':content
    })
if '--images-only' not in __import__('sys').argv:
    (ROOT/'new_articles.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('articles',len(records),'images',len(list(OUT.glob('*.webp'))),'words',sum(len(r['content'].split()) for r in records),'photo entries',[(r['slug'],r['content'].count('![')+1) for r in records])