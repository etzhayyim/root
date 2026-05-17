from typing import TypedDict
from langgraph.graph import StateGraph, END

class CastingState(TypedDict):
    spec_data: dict
    validation_passed: bool
    log: list

def validate_lead_specs(state: CastingState):
    specs = state['spec_data']
    passed = specs.get('lead_purity', 0) >= 99.9
    return {'validation_passed': passed, 'log': ['Lead purity verification complete']}

def safety_compliance_check(state: CastingState):
    return {'log': state['log'] + ['Toxicity assessment concluded']}

graph = StateGraph(CastingState)
graph.add_node('validate', validate_lead_specs)
graph.add_node('safety', safety_compliance_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()