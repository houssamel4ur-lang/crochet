"""Five provider-supplied HB Agency placements (keep all five distinct)."""
import re

TOP = "<div id='hbagency_space_349628'></div>"
INPAGE = "<div class=\"hb-ad-inpage\">\n    <div class=\"hb-ad-inner\"> \n    <div class=\"hbagency_cls hbagency_space_349630\"></div></div> </div>"
BOTTOM = "<div id='hbagency_space_349629'></div>"
FOOTER = "<div  id='HB_Footer_Close_hbagency_space_349627'>\n <div id='HB_CLOSE_hbagency_space_349627'></div>\n <div id='HB_OUTER_hbagency_space_349627'>\n<div id='hbagency_space_349627'></div>\n </div></div>\n<div  id='HB_Footer_Close_hbagency_space_349626'>\n <div id='HB_CLOSE_hbagency_space_349626'></div>\n <div id='HB_OUTER_hbagency_space_349626'>\n<div id='hbagency_space_349626'></div>\n </div></div>"

def inject_hb_ads(page):
    """Place 3 in-content slots and 2 floating footer slots in generated pages."""
    start = page.find('<main id="content"><article')
    end = page.find('</article></main>', start)
    if start < 0 or end < 0:
        raise ValueError("HB Agency: article anchors missing")
    if "hbagency_space_349628" in page:
        return page
    content = page[start:end]
    cover = re.search(r'<img class="article-cover"[^>]*>', content)
    para = re.search(r'<p(?:\s[^>]*)?>[\s\S]*?</p>', content)
    if cover:
        pos = cover.end()
    elif para:
        pos = para.end()
    else:
        raise ValueError("HB Agency: article has no cover or paragraph")
    content = content[:pos] + "\n" + TOP + content[pos:]
    headings = list(re.finditer(r'<h2(?:\s|>)', content))
    middle = headings[len(headings) // 2].start() if headings else len(content)
    content = content[:middle] + INPAGE + "\n" + content[middle:]
    bottom = content.find('<section class="related-posts"')
    if bottom == -1:
        bottom = content.find('<h2>Keep Creating</h2>')
    if bottom == -1:
        bottom = len(content)
    content = content[:bottom] + BOTTOM + "\n" + content[bottom:]
    page = page[:start] + content + page[end:]
    if '</body>' not in page:
        raise ValueError("HB Agency: body closing tag missing")
    return page.replace('</body>', FOOTER + "\n</body>")
