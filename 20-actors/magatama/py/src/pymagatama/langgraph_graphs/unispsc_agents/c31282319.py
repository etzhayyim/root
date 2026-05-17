from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class ZincState(TypedDict):
    spec_data: dict
    validation_passed: bool
    log: list

def validate_zinc_stretch_specs(state: ZincState):
    specs = state['spec_data']
    passed = 'alloy_grade' in specs and 'tolerance_mm' in specs
    return {'validation_passed': passed, 'log': ['Material spec validated'] if passed else ['Validation failed']}

def route_by_validation(state: ZincState):
    return 'process' if state['validation_passed'] else END

graph = StateGraph(ZincState)
graph.add_node('validate', validate_zinc_stretch_specs)
graph.add_node('process', lambda x: {'log': x['log'] + ['Processing stretch formed zinc parts']})
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_validation)
graph.add_edge('process', END)
graph = graph.compile()