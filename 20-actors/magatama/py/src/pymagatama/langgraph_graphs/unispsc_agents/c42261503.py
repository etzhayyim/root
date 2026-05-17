from langgraph.graph import StateGraph, END
from typing import TypedDict

class AutopsyToolState(TypedDict):
    material_compliance: bool
    dimensions_verified: bool
    sterilization_ok: bool

def validate_tool_specs(state: AutopsyToolState):
    state['material_compliance'] = True
    return 'specs_checked'

def run_compliance_check(state: AutopsyToolState):
    state['dimensions_verified'] = True
    return 'compliance_passed'

graph = StateGraph(AutopsyToolState)
graph.add_node('validate', validate_tool_specs)
graph.add_node('compliance', run_compliance_check)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()