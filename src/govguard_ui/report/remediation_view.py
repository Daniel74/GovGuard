"""Measure proposal in the report "nach Fundstelle": the request from the component and the
proposals kept in the session (#82). The view only shows: what asks the model, and for the
password, is a hook (`Proposer`) a page hands in (screens/measure_runner.py); without it the
report has no button. Findings, report and document stay unchanged."""

from collections.abc import Callable
from functools import partial
from typing import NamedTuple

import streamlit as st

from govguard.checks.remediation import offers_measures
from govguard.checks.sites import Site, Sites
from govguard_ui.report.remediation_data import (
    Proposals,
    document_digest,
    proposal_basis,
    suggest_data,
)


class Proposer(NamedTuple):
    run: Callable[[Site, str, str], None]  # (site, document, report key): password, model call
    unlocked: Callable[[], bool]  # the session gave the password: no dialog, the notice stands
    notice: str  # what leaves the app, under the button once the dialog is gone


def _pending(key: str) -> str:
    return f"{key}_suggest_pending"


def _proposals_key(key: str) -> str:
    return f"{key}_measures"


def proposals(key: str) -> Proposals:
    """The proposals of one report in this session: site -> measures (None: none possible)."""
    return st.session_state.setdefault(_proposals_key(key), {})


def forget_proposals(key: str) -> None:
    """A new report under the same key (Audit erstellen) starts without proposals."""
    st.session_state.pop(_proposals_key(key), None)


def component_suggest(
    key: str, text: str, propose: Proposer | None, everything: Sites,
) -> Callable[[Site], dict | None]:
    """For site_data: button and proposal of a site, as the session stands now. everything: the
    sites of the whole report, unfiltered: a proposal covers all WARN/FAIL of its site."""
    if propose is None:
        return lambda site: None  # no hook, no button
    note = propose.notice if propose.unlocked() else ""
    data = partial(suggest_data, stored=proposals(key), note=note, digest=document_digest(text))
    return lambda site: data(proposal_basis(site, everything))


def request(key: str, state: str) -> None:
    """Callback of the component's `suggest` event: remember the site, the script run reacts."""
    if (index := st.session_state[state].suggest) is not None:
        st.session_state[_pending(key)] = int(index)


def handle_request(
    sites: Sites, everything: Sites, text: str, key: str, propose: Proposer | None,
) -> None:
    """After the component: hand a requested site, with all its findings, to the page's hook."""
    index = st.session_state.pop(_pending(key), None)
    if propose is None or index is None or not 0 <= index < len(sites.placed):
        return
    site = proposal_basis(sites.placed[index], everything)
    if offers_measures(site):
        propose.run(site, text, key)
