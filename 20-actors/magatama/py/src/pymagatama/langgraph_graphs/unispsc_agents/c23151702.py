from langgraph.graph import StateGraph
from typing import TypedDict, Dict, Any
class WeldingState(TypedDict):
    spec_data: Dict[str, Any]
    validation_passed: bool
def validate_laser_specs(state: WeldingState) -> WeldingState:
    safety_rating = state['spec_data'].get('Laser Class Rating', 1)
    state['validation_passed'] = safety_rating >= 4
    return state
def trigger_export_check(state: WeldingState) -> WeldingState:
    print('Checking dual-use export controls...')
    return state
graph = StateGraph(WeldingState)
graph.add_node('validate', validate_laser_specs)
graph.add_node('export_review', trigger_export_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export_review')
graph.set_finish_point('export_review')
graph = graph.compile()