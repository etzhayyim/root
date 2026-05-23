from typing import TypedDict
from langgraph.graph import StateGraph, END
class MaterialState(TypedDict):
    material_type: str
    spec_complaint: bool
    inspection_result: str
def validate_integrity(state: MaterialState):
    print(f'Validating {state["material_type"]} specs...')
    state['spec_complaint'] = True
    return state
def check_compliance(state: MaterialState):
    state['inspection_result'] = 'PASSED' if state['spec_complaint'] else 'FAILED'
    return state
graph = StateGraph(MaterialState)
graph.add_node('validate', validate_integrity)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
