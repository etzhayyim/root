from typing import TypedDict
from langgraph.graph import StateGraph, END
class IncubatorState(TypedDict):
    specs: dict
    validation_status: bool
def validate_specs(state: IncubatorState):
    has_stability = 'TemperatureStabilityAccuracy' in state['specs']
    return {'validation_status': has_stability}
def compliance_check(state: IncubatorState):
    print('Checking regulatory compliance for medical incubator...')
    return 'COMPLIANT' if state['validation_status'] else 'INVALID'
graph = StateGraph(IncubatorState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', compliance_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
