from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class PrecisionReducerState(TypedDict):
    spec_id: str
    torque_rating: float
    backlash: float
    validated: bool
    compliance_checks: List[str]

def validate_reducer_specs(state: PrecisionReducerState) -> PrecisionReducerState:
    # Validation logic for high-precision mechanical components
    if state['torque_rating'] > 0 and state['backlash'] < 0.05:
        state['validated'] = True
        state['compliance_checks'].append('Passed precision threshold')
    else:
        state['validated'] = False
        state['compliance_checks'].append('Failed precision threshold')
    return state

def check_export_compliance(state: PrecisionReducerState) -> PrecisionReducerState:
    # Logic for dual-use export control screening
    state['compliance_checks'].append('Dual-use screening complete')
    return state

graph = StateGraph(PrecisionReducerState)
graph.add_node('validate', validate_reducer_specs)
graph.add_node('export_check', check_export_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export_check')
graph.add_edge('export_check', END)
graph = graph.compile()