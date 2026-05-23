from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ProcurementState(TypedDict):
    kit_components: List[str]
    sterility_date: str
    is_compliant: bool

def validate_components(state: ProcurementState):
    required = ['antiseptic_swab', 'gauze', 'adhesive_dressing']
    all_present = all(item in state['kit_components'] for item in required)
    return {'is_compliant': all_present}

def update_compliance(state: ProcurementState):
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_components)
graph.add_node('compliance', update_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
