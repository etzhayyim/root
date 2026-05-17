from langgraph.graph import StateGraph, END
from typing import TypedDict
class VeneerState(TypedDict):
    serial_number: str
    material_spec: dict
    is_compliant: bool
def validate_material(state: VeneerState):
    state['is_compliant'] = state['material_spec'].get('iso_grade') == 'Class 5'
    return state
def check_regulatory_status(state: VeneerState):
    print(f'Checking FDA/MDR status for serial {state['serial_number']}')
    return 'regulatory_check_complete'
graph = StateGraph(VeneerState)
graph.add_node('validate', validate_material)
graph.add_node('regulatory', check_regulatory_status)
graph.set_entry_point('validate')
graph.add_edge('validate', 'regulatory')
graph.add_edge('regulatory', END)
compile_graph = graph.compile()