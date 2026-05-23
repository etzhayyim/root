from typing import TypedDict
from langgraph.graph import StateGraph, END

class RavioliMakerState(TypedDict):
    spec_sheet: str
    compliance_ok: bool
    approved: bool

def validate_specs(state: RavioliMakerState):
    print('Validating food-grade materials...')
    return {'compliance_ok': 'food-grade' in state['spec_sheet'].lower()}

def final_approval(state: RavioliMakerState):
    return {'approved': state['compliance_ok']}

graph = StateGraph(RavioliMakerState)

graph.add_node('validate', validate_specs)
graph.add_node('approve', final_approval)

graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)

graph = graph.compile()
