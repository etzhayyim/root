from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class PreciousMetalState(TypedDict):
    material_spec: dict
    validation_logs: Annotated[Sequence[str], operator.add]
    is_compliant: bool

def validate_purity(state: PreciousMetalState):
    purity = state['material_spec'].get('purity', 0)
    if purity >= 99.9:
        return {'validation_logs': ['Purity verified at ultra-high level'], 'is_compliant': True}
    return {'validation_logs': ['Purity insufficient for precision industrial use'], 'is_compliant': False}

def check_origin_risk(state: PreciousMetalState):
    if state['material_spec'].get('origin') in ['sanctioned_region']:
        return {'validation_logs': ['CRITICAL: Origin risk flagged'], 'is_compliant': False}
    return {'validation_logs': ['Origin verification passed'], 'is_compliant': state['is_compliant']}

graph = StateGraph(PreciousMetalState)
graph.add_node('purity_check', validate_purity)
graph.add_node('origin_check', check_origin_risk)
graph.set_entry_point('purity_check')
graph.add_edge('purity_check', 'origin_check')
graph.add_edge('origin_check', END)
graph = graph.compile()
