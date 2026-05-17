from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class VapCanisterState(TypedDict):
    part_id: str
    adsorption_capacity: float
    compliance_docs: List[str]
    approved: bool

def validate_specs(state: VapCanisterState) -> VapCanisterState:
    state['approved'] = state['adsorption_capacity'] > 0 and len(state['compliance_docs']) > 0
    return state

def execute_qc(state: VapCanisterState) -> VapCanisterState:
    print(f'Checking emissions compliance for: {state["part_id"]}')
    return state

graph = StateGraph(VapCanisterState)
graph.add_node('validate', validate_specs)
graph.add_node('qc', execute_qc)
graph.set_entry_point('validate')
graph.add_edge('validate', 'qc')
graph.add_edge('qc', END)
graph = graph.compile()