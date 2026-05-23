from typing import TypedDict
from langgraph.graph import StateGraph, END

class SteelChannelState(TypedDict):
    spec_data: dict
    validated: bool
    error_log: list

def validate_specs(state: SteelChannelState):
    required = ['material_grade_standard', 'yield_strength_mpa']
    missing = [f for f in required if f not in state['spec_data']]
    return {'validated': len(missing) == 0, 'error_log': missing}

def structural_compliance(state: SteelChannelState):
    if state.get('validated'):
        print('Conducting mechanical strength verification...')
    return state

graph = StateGraph(SteelChannelState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', structural_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
