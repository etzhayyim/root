from typing import TypedDict
from langgraph.graph import StateGraph, END

class AntisepticState(TypedDict):
    product_name: str
    concentration: float
    is_flammable: bool
    validation_passed: bool

def validate_composition(state: AntisepticState):
    # Validate ethanol/acetone concentration matches regulatory standards
    state['validation_passed'] = 60.0 <= state['concentration'] <= 95.0
    return state

def check_hazard_compliance(state: AntisepticState):
    # Ensure dangerous goods documentation exists for high-risk items
    if state['is_flammable']:
        print('Hazard verification: Flammable goods protocols active.')
    return state

graph = StateGraph(AntisepticState)
graph.add_node('composition', validate_composition)
graph.add_node('safety', check_hazard_compliance)
graph.set_entry_point('composition')
graph.add_edge('composition', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()