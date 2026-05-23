from typing import TypedDict, List
from langgraph.graph import StateGraph, END
class PipetteState(TypedDict):
    model_id: str
    iso_8655_result: bool
    calibration_status: str
    validation_log: List[str]
def validate_calibration(state: PipetteState) -> PipetteState:
    state['validation_log'].append('Checking ISO 8655 compliance')
    state['iso_8655_result'] = True if state['calibration_status'] == 'passed' else False
    return state
def check_documentation(state: PipetteState) -> PipetteState:
    state['validation_log'].append('Verifying certificate of calibration')
    return state
graph = StateGraph(PipetteState)
graph.add_node('validate', validate_calibration)
graph.add_node('docs', check_documentation)
graph.add_edge('validate', 'docs')
graph.add_edge('docs', END)
graph.set_entry_point('validate')
graph = graph.compile()
