from typing import TypedDict
from langgraph.graph import StateGraph, END

class ChainProcurementState(TypedDict):
    spec_data: dict
    validation_results: list
    is_approved: bool

def validate_specs(state: ChainProcurementState):
    valid = all(key in state['spec_data'] for key in ['material_grade', 'pitch_size'])
    return {'validation_results': ['Specs presence check: ' + str(valid)], 'is_approved': valid}

def safety_check(state: ChainProcurementState):
    if state.get('is_approved'):
        return {'is_approved': state['spec_data'].get('safety_certification', False)}
    return {'is_approved': False}

graph = StateGraph(ChainProcurementState)
graph.add_node('validate', validate_specs)
graph.add_node('safety', safety_check)
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph.set_entry_point('validate')
graph = graph.compile()
