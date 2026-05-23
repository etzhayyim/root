from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DentalState(TypedDict):
    product_id: str
    specifications: dict
    is_compliant: bool
    validation_log: List[str]

def validate_sterility(state: DentalState):
    sal = state['specifications'].get('sal', 0)
    state['is_compliant'] = sal >= 6
    state['validation_log'].append(f'Sterility check: SAL {sal}')
    return state

def check_dimensions(state: DentalState):
    taper = state['specifications'].get('taper', 0)
    if 0.02 <= taper <= 0.06:
        state['validation_log'].append('Taper within standard ISO tolerance')
    else:
        state['is_compliant'] = False
    return state

graph = StateGraph(DentalState)
graph.add_node('validate_sterility', validate_sterility)
graph.add_node('check_dimensions', check_dimensions)
graph.set_entry_point('validate_sterility')
graph.add_edge('validate_sterility', 'check_dimensions')
graph.add_edge('check_dimensions', END)
app = graph.compile()
