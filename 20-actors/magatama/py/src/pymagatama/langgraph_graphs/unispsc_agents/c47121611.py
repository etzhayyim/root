from langgraph.graph import StateGraph, END
from typing import TypedDict
class ScraperState(TypedDict):
    model: str
    blade_material: str
    power_type: str
    is_compliant: bool
def validate_scraper(state: ScraperState):
    state['is_compliant'] = state['blade_material'] in ['Hardened Steel', 'Stainless Steel']
    return state
def procurement_routing(state: ScraperState):
    return 'process' if state['is_compliant'] else 'reject'
graph = StateGraph(ScraperState)
graph.add_node('validate', validate_scraper)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', procurement_routing, {'process': END, 'reject': END})
graph.compile()