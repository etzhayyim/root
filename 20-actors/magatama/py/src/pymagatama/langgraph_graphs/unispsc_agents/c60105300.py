from typing import TypedDict
from langgraph.graph import StateGraph, END

class CareerEdState(TypedDict):
    materials_list: list
    compliance_check: bool
    finalized: bool

def validate_material(state: CareerEdState):
    state['compliance_check'] = all('cert_id' in m for m in state['materials_list'])
    print('Validating pedagogical standards...')
    return state

def finalize_order(state: CareerEdState):
    state['finalized'] = state['compliance_check']
    return state

graph = StateGraph(CareerEdState)
graph.add_node('validate', validate_material)
graph.add_node('finalize', finalize_order)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()