"""PROTOTYPE #81 – variant B: one expander per site with the findings as a list of measures;
throwaway, only on branch prototype/81-fundstelle."""

from collections.abc import Callable

import streamlit as st

from govguard.models import Finding
from govguard_ui.report.finding_detail import plain
from govguard_ui.report.prototype_81_sites import Site, mix_text, site_of
from govguard_ui.report.review import category
from govguard_ui.style import LOOKS, badge, paragraph

QUOTE = 180


def render_site_cards(sites: list[Site], selected: Finding, key: str,
                      on_select: Callable[[str], None]) -> None:
    home = site_of(sites, selected)
    with st.container(height=560, border=False):
        for site in sites:
            look = LOOKS[site.worst]
            label = f"{look.symbol} {site.lines} · {len(site.findings)} Befunde · {mix_text(site)}"
            with st.expander(label, expanded=site is home, key=f"{key}_p81_{site.id}"):
                st.caption(" · ".join(plain(a) for a in site.anchors))
                if quote := next((f.evidence for f in site.findings if f.evidence), None):
                    short = quote if len(quote) <= QUOTE else quote[:QUOTE] + " …"
                    st.html(f'<blockquote style="margin:0;color:#4A5361">'
                            f"{paragraph(short)}</blockquote>")
                for finding in site.findings:
                    _measure(finding, finding is selected, key, on_select)


def _measure(finding: Finding, chosen: bool, key: str, on_select: Callable[[str], None]) -> None:
    with st.container(border=chosen, horizontal=False, gap="small"):
        with st.container(horizontal=True, vertical_alignment="center", gap="small"):
            st.html(badge(category(finding)), width="content")
            st.button(plain(finding.title), key=f"{key}_p81_pick_{finding.rule_id}",
                      type="tertiary", on_click=on_select, args=(finding.rule_id,))
        if finding.recommendation:
            st.html(f'<div style="font-size:14px;color:#4A5361"><b>Empfehlung:</b> '
                    f"{paragraph(finding.recommendation)[3:-4]}</div>")
