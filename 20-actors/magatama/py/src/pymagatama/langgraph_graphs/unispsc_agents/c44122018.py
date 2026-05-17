from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class FileSupplyState(TypedDict):
    supply_id: str
    spec_check: bool
    compliance_passed: bool

def validate_dimensions(state: FileSupplyState):
    print(f'Validating dimensions for {state["supply_id"]}')
    return {'spec_check': True}

def verify_compliance(state: FileSupplyState):
    print('Checking standard office supply compliance')
    return {'compliance_passed': True}

graph = StateGraph(FileSupplyState)
graph.add_node('validate', validate_dimensions)
graph.add_node('compliance', verify_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()