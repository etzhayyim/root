from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ProteinAnalysisState(TypedDict):
    sample_id: str
    spec_requirements: dict
    validation_status: bool
    error_log: List[str]

def validate_tech_specs(state: ProteinAnalysisState):
    required = ['detection_sensitivity', 'calibration']
    if all(k in state['spec_requirements'] for k in required):
        return {'validation_status': True}
    return {'validation_status': False, 'error_log': ['Missing technical specifications']}

def route_by_validation(state: ProteinAnalysisState):
    return 'validate' if not state.get('validation_status') else END

graph = StateGraph(ProteinAnalysisState)
graph.add_node('validate', validate_tech_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
