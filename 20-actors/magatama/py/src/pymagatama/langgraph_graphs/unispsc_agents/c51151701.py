from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PharmState(TypedDict):
    product_name: str
    quality_docs: List[str]
    is_compliant: bool

def validate_gmp(state: PharmState) -> PharmState:
    state['is_compliant'] = 'GMP_CERT' in state['quality_docs']
    return state

def check_temp(state: PharmState) -> PharmState:
    if state['is_compliant']:
        print('Logistics: Verifying cold chain requirements...')
    return state

graph = StateGraph(PharmState)
graph.add_node('validate', validate_gmp)
graph.add_node('logistics', check_temp)
graph.add_edge('validate', 'logistics')
graph.add_edge('logistics', END)
graph.set_entry_point('validate')
graph = graph.compile()
