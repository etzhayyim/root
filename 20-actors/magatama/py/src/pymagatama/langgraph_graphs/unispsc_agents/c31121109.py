from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class CastingsState(TypedDict):
    part_specs: dict
    validation_report: List[str]

def validate_specs(state: CastingsState):
    report = []
    if state['part_specs'].get('precision') < 0.05:
        report.append('Tolerance passed')
    else:
        report.append('Tolerance failed - outside limits')
    return {'validation_report': report}

def finalize_order(state: CastingsState):
    return {'validation_report': state['validation_report'] + ['Order ready for foundry']}

graph = StateGraph(CastingsState)
graph.add_node('validate', validate_specs)
graph.add_node('finalize', finalize_order)
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph.set_entry_point('validate')
graph = graph.compile()