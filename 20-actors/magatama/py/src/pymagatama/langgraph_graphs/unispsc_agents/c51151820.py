from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    material_name: str
    purity: float
    compliance_passed: bool

def validate_purity(state: ProcurementState):
    if state['purity'] >= 99.0:
        return {'compliance_passed': True}
    return {'compliance_passed': False}

def check_regulatory(state: ProcurementState):
    print(f'Checking {state['material_name']} against controlled substance list...')
    return {'compliance_passed': True}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_purity)
graph.add_node('regulatory', check_regulatory)
graph.set_entry_point('validate')
graph.add_edge('validate', 'regulatory')
graph.add_edge('regulatory', END)
graph = graph.compile()
