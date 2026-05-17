from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class FloorPolishState(TypedDict):
    product_name: str
    safety_certs: List[str]
    compliance_score: float

def validate_safety_data(state: FloorPolishState):
    state['compliance_score'] = 1.0 if 'MSDS' in state['safety_certs'] else 0.0
    return 'valid' if state['compliance_score'] > 0 else 'error'

def finalize_procurement(state: FloorPolishState):
    print(f'Finalizing procurement for {state.get("product_name")}')

graph = StateGraph(FloorPolishState)
graph.add_node('validate', validate_safety_data)
graph.add_node('finalize', finalize_procurement)
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph.set_entry_point('validate')
graph = graph.compile()