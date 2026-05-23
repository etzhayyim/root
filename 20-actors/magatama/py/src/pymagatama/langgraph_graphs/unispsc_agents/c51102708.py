from typing import TypedDict
from langgraph.graph import StateGraph, END

class AntisepticState(TypedDict):
    concentration: float
    safety_clearance: bool
    is_compliant: bool

def validate_safety(state: AntisepticState):
    # Business logic for dangerous goods validation
    state['safety_clearance'] = state['concentration'] <= 37.0
    return {'safety_clearance': state['safety_clearance']}

def check_compliance(state: AntisepticState):
    state['is_compliant'] = state['safety_clearance']
    return {'is_compliant': state['is_compliant']}

graph = StateGraph(AntisepticState)
graph.add_node('validate', validate_safety)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph_compiled = graph.compile()
