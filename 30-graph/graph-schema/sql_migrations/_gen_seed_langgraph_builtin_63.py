"""Generate seed SQL for all 63 builtin LangGraph assistants."""
from __future__ import annotations

# (assistant_id, factory_path)
# 55 standard graphs + 8 single-task + 1 echo = 64
ROWS = [
    # standard module.build_graph()
    ("adsk_ingest_dataset", "pymagatama.langgraph_graphs.adsk_ingest_dataset"),
    ("agent_runtime_lease_autopilot", "pymagatama.langgraph_graphs.agent_runtime_lease_autopilot"),
    ("animeka_autopilot", "pymagatama.langgraph_graphs.animeka_autopilot"),
    ("aria_attention_ingest", "pymagatama.langgraph_graphs.aria_attention_ingest"),
    ("aria_emotion_ingest", "pymagatama.langgraph_graphs.aria_emotion_ingest"),
    ("aria_influence_ingest", "pymagatama.langgraph_graphs.aria_influence_ingest"),
    ("aria_market_ingest", "pymagatama.langgraph_graphs.aria_market_ingest"),
    ("aria_minimax_sweep", "pymagatama.langgraph_graphs.aria_minimax_sweep"),
    ("aria_money_flow_ingest", "pymagatama.langgraph_graphs.aria_money_flow_ingest"),
    ("aria_request_ingest", "pymagatama.langgraph_graphs.aria_request_ingest"),
    ("copyright_fulltext", "pymagatama.langgraph_graphs.copyright_fulltext"),
    ("copyright_ingest", "pymagatama.langgraph_graphs.copyright_ingest"),
    ("coverage_gap_bridge", "pymagatama.langgraph_graphs.coverage_gap_bridge"),
    ("echo", "pymagatama.langgraph_graphs.echo"),
    ("gftdcojp-company-ops", "pymagatama.langgraph_graphs.gftdcojp_company_ops"),
    ("isbn_ingest_aozora", "pymagatama.langgraph_graphs.isbn_ingest_aozora"),
    ("isbn_ingest_gutenberg", "pymagatama.langgraph_graphs.isbn_ingest_gutenberg"),
    ("isbn_ingest_hathitrust", "pymagatama.langgraph_graphs.isbn_ingest_hathitrust"),
    ("isbn_ingest_internet_archive", "pymagatama.langgraph_graphs.isbn_ingest_internet_archive"),
    ("isbn_ingest_ndl", "pymagatama.langgraph_graphs.isbn_ingest_ndl"),
    ("isbn_ingest_open_library", "pymagatama.langgraph_graphs.isbn_ingest_open_library"),
    ("kaisya-member-assistant", "pymagatama.langgraph_graphs.kaisya_member_assistant"),
    ("ki.cycle.v1", "pymagatama.langgraph_graphs.ki_cycle"),
    ("ki.synthesize.v1", "pymagatama.primitives.ki_synthesis_graph:_build_graph"),
    ("koke.cycle.v1", "pymagatama.langgraph_graphs.koke_cycle"),
    ("lawfirm-marketing-ops", "pymagatama.langgraph_graphs.lawfirm_marketing_ops"),
    ("newsletter_send_campaign", "pymagatama.newsletter_worker_main:build_newsletter_graph"),
    ("onion_crawl_seeds", "pymagatama.langgraph_graphs.onion_crawl_seeds"),
    ("os_messaging_crawl_open_channels", "pymagatama.langgraph_graphs.os_messaging_crawl_open_channels"),
    ("patent_blob_convert", "pymagatama.langgraph_graphs.patent_blob_convert"),
    ("patent_ingest_uspto_weekly", "pymagatama.langgraph_graphs.patent_ingest_uspto_weekly"),
    ("public_malak_crawl_ads", "pymagatama.langgraph_graphs.public_malak_crawl_ads"),
    ("saikin.cycle.v1", "pymagatama.langgraph_graphs.saikin_cycle"),
    ("shinka_cron_tick", "pymagatama.langgraph_graphs.shinka_cron_tick"),
    ("shinshi_seed_gap_fill", "pymagatama.langgraph_graphs.shinshi_seed_gap_fill"),
    ("shosha_agent_loop", "pymagatama.langgraph_graphs.shosha_agent_loop"),
    ("shosha_daily_report", "pymagatama.langgraph_graphs.shosha_daily_report"),
    ("shosha_market_intelligence", "pymagatama.langgraph_graphs.shosha_market_intelligence"),
    ("shosha_react_upstream", "pymagatama.langgraph_graphs.shosha_react_upstream"),
    ("shosha_refresh_sanctions_list", "pymagatama.langgraph_graphs.shosha_refresh_sanctions_list"),
    ("shosha_trade_book_recompute", "pymagatama.langgraph_graphs.shosha_trade_book_recompute"),
    ("shosha_trade_idea_synthesize", "pymagatama.langgraph_graphs.shosha_trade_idea_synthesize"),
    ("tsukuru_isic_pulse", "pymagatama.langgraph_graphs.tsukuru_isic_pulse"),
    ("webmk_create_proposal", "pymagatama.langgraph_graphs.webmk_proposal"),
    ("wellbecoming_belief_influence_propagate", "pymagatama.langgraph_graphs.wellbecoming_belief_influence_propagate"),
    ("wellbecoming_belief_noise_inject", "pymagatama.langgraph_graphs.wellbecoming_belief_noise_inject"),
    ("wellbecoming_belief_restoring_capture", "pymagatama.langgraph_graphs.wellbecoming_belief_restoring_capture"),
    ("wellbecoming_detect_bottleneck", "pymagatama.langgraph_graphs.wellbecoming_detect_bottleneck"),
    ("wellbecoming_floor_violation_alert", "pymagatama.langgraph_graphs.wellbecoming_floor_violation_alert"),
    ("wellbecoming_minimax_sweep", "pymagatama.langgraph_graphs.wellbecoming_minimax_sweep"),
    ("wellbecoming_proactive_connect", "pymagatama.langgraph_graphs.wellbecoming_proactive_connect"),
    ("wellbecoming_process_mining", "pymagatama.langgraph_graphs.wellbecoming_process_mining"),
    ("wellbecoming_trust_weight_update", "pymagatama.langgraph_graphs.wellbecoming_trust_weight_update"),
    ("yoro_platform_pulse", "pymagatama.langgraph_graphs.yoro_platform_pulse"),
    ("yoro_product_ingest", "pymagatama.langgraph_graphs.yoro_product_ingest"),
    # 8 single-task wrappers via _single_task_wrapper named factories
    ("kobo.budAgent.v1",       "pymagatama.langgraph_graphs._single_task_wrapper:build_graph_kobo_budAgent"),
    ("kobo.sporulate.v1",      "pymagatama.langgraph_graphs._single_task_wrapper:build_graph_kobo_sporulate"),
    ("kobo.germinate.v1",      "pymagatama.langgraph_graphs._single_task_wrapper:build_graph_kobo_germinate"),
    ("kabi.fusionProbe.v1",    "pymagatama.langgraph_graphs._single_task_wrapper:build_graph_kabi_fusionProbe"),
    ("kinoko.formBlock.v1",    "pymagatama.langgraph_graphs._single_task_wrapper:build_graph_kinoko_formBlock"),
    ("hakkou.createFerment.v1", "pymagatama.langgraph_graphs._single_task_wrapper:build_graph_hakkou_createFerment"),
    ("hakkou.llmTransform.v1",  "pymagatama.langgraph_graphs._single_task_wrapper:build_graph_hakkou_llmTransform"),
    ("hakkou.finalizeFerment.v1","pymagatama.langgraph_graphs._single_task_wrapper:build_graph_hakkou_finalizeFerment"),
]


def gen_sql() -> str:
    out = [
        "-- Auto-generated seed for 63 builtin LangGraph assistants (P1a).",
        "-- ADR-2605080600 — drops the static _register_builtin_graphs() block.",
        "-- All rows use kind='py_factory'; topology migration is per-actor follow-up.",
        "",
    ]
    for aid, mod in ROWS:
        # Escape single quotes in assistant_id (none expected, but defensive).
        aid_sql = aid.replace("'", "''")
        mod_sql = mod.replace("'", "''")
        out.append(
            "INSERT INTO vertex_langgraph_assistant (vertex_id, _seq, sensitivity_ord, "
            "assistant_id, version, kind, factory_path, description, created_at) "
            f"VALUES ('{aid_sql}', 0, 0, '{aid_sql}', 1, 'py_factory', '{mod_sql}', "
            f"'auto-seeded P1a', '2026-05-08T16:00:00Z');"
        )
    out.append("")
    for aid, _mod in ROWS:
        aid_sql = aid.replace("'", "''")
        # nsid mirror for now; per-actor real NSIDs added in subsequent migration.
        nsid = f"langgraph.builtin.{aid_sql}"
        out.append(
            "INSERT INTO vertex_langgraph_deployment (vertex_id, _seq, sensitivity_ord, "
            "nsid, assistant_id, version, status, replicas, updated_at) "
            f"VALUES ('{nsid}', 0, 0, '{nsid}', '{aid_sql}', 1, 'active', 1, "
            f"'2026-05-08T16:00:00Z');"
        )
    return "\n".join(out)


if __name__ == "__main__":
    print(gen_sql())
    print(f"\n-- {len(ROWS)} assistants, {len(ROWS)} deployments")
