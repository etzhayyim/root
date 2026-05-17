from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CastingState(TypedDict):
    specs: dict
    validation_report: List[str]
    approved: bool

def validate_alloy_specs(state: CastingState):
    report = []
    if 'alloy_composition' not in state['specs']:
        report.append('Missing Alloy Composition')
    return {'validation_report': report, 'approved': len(report) == 0}

def ndt_inspection_step(state: CastingState):
    return {'validation_report': state['validation_report'] + ['NDT_Passed']}

graph = StateGraph(CastingState)
graph.add_node('validate', validate_alloy_specs)
graph.add_node('inspection', ndt_inspection_step)
graph.set_entry_point('validate')
graph.add_edge('validate', 'inspection')
graph.add_edge('inspection', END)
app = graph.compile()