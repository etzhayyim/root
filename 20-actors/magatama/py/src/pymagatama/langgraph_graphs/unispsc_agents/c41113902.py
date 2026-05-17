from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DissolutionState(TypedDict):
    device_id: str
    calib_data: dict
    is_compliant: bool
    errors: List[str]

def validate_specs(state: DissolutionState):
    # Simulate USP compliance logic
    temp_ok = state['calib_data'].get('temp', 0) == 37.0
    state['is_compliant'] = temp_ok
    if not temp_ok:
        state['errors'].append('Temperature deviation detected')
    return state

workflow = StateGraph(DissolutionState)
workflow.add_node('validate', validate_specs)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()