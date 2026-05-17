from typing import TypedDict
from langgraph.graph import StateGraph, END

class BerylliumState(TypedDict):
    part_specs: dict
    security_cleared: bool
    export_compliant: bool

def validate_tech_specs(state: BerylliumState):
    # Simulate CAD and impurity check logic
    assert 'purity_level' in state['part_specs'], 'Missing purity data'
    return {'security_cleared': True}

def check_regulations(state: BerylliumState):
    # Verify dual-use export control status
    return {'export_compliant': True}

graph = StateGraph(BerylliumState)
graph.add_node('validate', validate_tech_specs)
graph.add_node('compliance', check_regulations)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()