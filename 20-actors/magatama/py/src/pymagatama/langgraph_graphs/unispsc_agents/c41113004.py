from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class AnalysisState(TypedDict):
    analyzer_specs: dict
    validation_logs: Annotated[Sequence[str], operator.add]
    is_compliant: bool

def validate_fid_specs(state: AnalysisState):
    specs = state['analyzer_specs']
    logs = []
    if 'detection_limit' not in specs:
        logs.append('Missing mandatory detection limit.')
    return {'validation_logs': logs, 'is_compliant': len(logs) == 0}

def route_by_compliance(state: AnalysisState):
    return 'valid' if state['is_compliant'] else 'reject'

graph = StateGraph(AnalysisState)
graph.add_node('validate', validate_fid_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph.compile()