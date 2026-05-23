from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class TitaniumState(TypedDict):
    part_specs: dict
    validation_passed: bool
    export_compliance: bool

def validate_specs(state: TitaniumState):
    # Simulate geometric and material validation
    passed = 'material_grade' in state['part_specs']
    return {'validation_passed': passed}

def check_compliance(state: TitaniumState):
    # Simulate dual-use export control checks
    return {'export_compliance': True}

graph = StateGraph(TitaniumState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
