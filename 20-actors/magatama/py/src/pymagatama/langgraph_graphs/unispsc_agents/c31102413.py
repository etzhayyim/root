from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CastingState(TypedDict):
    part_specs: dict
    validation_report: List[str]
    approved: bool

def validate_v_process_specs(state: CastingState):
    specs = state['part_specs']
    report = []
    if 'tolerance' not in specs or specs['tolerance'] > 0.05:
        report.append('Tolerance exceeds precision V-process limits')
    return {'validation_report': report, 'approved': len(report) == 0}

graph = StateGraph(CastingState)
graph.add_node('validate', validate_v_process_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()