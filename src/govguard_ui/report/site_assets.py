"""HTML and CSS of the document with its sites (CCv2): the bars in the margin, the box with the
findings under a site (#81); the script is in site_script. Colours come from LOOKS, the shadow
DOM sees no page CSS."""

from govguard_ui.style import LOOKS, badge_css

HTML = '<div class="doc"></div>'  # frame and head come from Streamlit, like the table view

_LOOKS_CSS = "".join(
    f".f-{look.css}{{background:{look.border};color:{look.text}}}"
    f".t-{look.css}{{background:{look.background}}}" for look in LOOKS.values())

CSS = """
.doc{font-family:'Source Code Pro',ui-monospace,monospace;font-size:13px;line-height:1.6;
  max-height:720px;overflow:auto;font-variant-ligatures:none;
  scrollbar-color:#A7AFBA transparent}
.l{display:grid;grid-template-columns:var(--lanes) 40px 1fr;gap:10px;white-space:pre-wrap;
  padding-right:12px}
.lanes{display:grid;grid-template-columns:repeat(var(--n),16px);gap:3px;padding-left:6px}
.bar{cursor:pointer;margin:0 3px}
.bar.top{border-radius:4px 4px 0 0;margin-top:3px}
.bar.end{border-radius:0 0 4px 4px;margin-bottom:3px}
.bar.top.end{border-radius:4px}
.bar span{display:block;font:700 10px/16px system-ui,sans-serif;text-align:center;margin:0 -3px}
.bar.cur{box-shadow:0 0 0 2px #0B4F8A}
.bar:hover{filter:brightness(.92)}
.bar:focus-visible,.item:focus-visible,button:focus-visible{outline:2px solid #0B4F8A}
.n{text-align:right;color:#4A5361}
.l.sel{background:#E3EEF9}
.l.sel .n{color:#0B4F8A;font-weight:700}
.l.hov{box-shadow:inset 0 0 0 999px rgba(11,79,138,.07)}
.l.click{cursor:pointer}
.box{font-family:system-ui,sans-serif;font-size:14px;line-height:1.5;margin:6px 12px 10px 60px;
  border:1px solid #0B4F8A;border-radius:8px;background:#FFFFFF}
.head{display:flex;gap:8px;align-items:center;padding:8px 12px;background:#E3EEF9;
  border-radius:7px 7px 0 0}
.head b{flex:1}
button{font:inherit;font-size:13px;border:1px solid #A7AFBA;background:#FFFFFF;
  border-radius:6px;padding:2px 10px;cursor:pointer}
button:disabled{cursor:default;color:#4A5361;opacity:.6}
.item{padding:10px 12px;border-top:1px solid #E3E7EC;cursor:pointer}
.item:hover{background:#F7F9FC}
.item.sel{background:#F2F6FB;box-shadow:inset 4px 0 #0B4F8A}
.item .t{font-weight:600}
.item .a{color:#4A5361;font-size:13px}
.item .w,.item .r{margin-top:4px}
.item .w::before{content:"Begründung: ";font-weight:600}
.item .r::before{content:"Empfehlung: ";font-weight:600}
.badge{display:inline-block;padding:0 6px;border:1px solid;border-radius:4px;font-size:13px;
  font-weight:600;margin-right:6px}
""" + _LOOKS_CSS + badge_css("b-")
