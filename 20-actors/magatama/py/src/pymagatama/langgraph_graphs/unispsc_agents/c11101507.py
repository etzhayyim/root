from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class RareEarthState(TypedDict):
    material_code: str
    purity: float
    compliance_cleared: bool
    log: List[str]

def validate_purity(state: RareEarthState):
    is_valid = state['purity'] >= 99.9
    return {'compliance_cleared': is_valid, 'log': [f'Purity check: {is_valid}']}

def export_control_check(state: RareEarthState):
    if state['compliance_cleared']:
        return {'log': ['Export control check passed']}
    return {'log': ['Export control flagged']}

def build_graph():
    graph = StateGraph(RareEarthState)
    graph.add_node('validate', validate_purity)
    graph.add_node('export_check', export_control_check)
    graph.set_entry_point('validate')
    graph.add_edge('validate', 'export_check')
    graph.add_edge('export_check', END)
    return graph.compile()

graph = build_graph()