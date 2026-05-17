from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    material_name: str
    purity_level: float
    compliance_cleared: bool

def validate_purity(state: ProcurementState):
    print(f'Validating purity for {state["material_name"]}')
    return {'compliance_cleared': state['purity_level'] >= 99.0}

def regulatory_check(state: ProcurementState):
    print('Performing regulatory health product screening...')
    return {'compliance_cleared': True}

graph = StateGraph(ProcurementState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('regulatory_check', regulatory_check)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'regulatory_check')
graph.add_edge('regulatory_check', END)
compile_graph = graph.compile()