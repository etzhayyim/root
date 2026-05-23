from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class FencingState(TypedDict):
    material_spec: str
    compliance_docs: List[str]
    approved: bool

def validate_material(state: FencingState):
    print('Validating metal fencing material grades...')
    state['approved'] = 'Galvanized' in state['material_spec']
    return state

def check_compliance(state: FencingState):
    print('Checking regulatory compliance requirements...')
    return {'compliance_docs': ['ASTM-F1083', 'ISO-9001']}

graph = StateGraph(FencingState)
graph.add_node('validate', validate_material)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
