from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class AssemblyState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    approved: bool

def validate_materials(state: AssemblyState):
    """Validate material compliance for copper assemblies."""
    if state['spec_data'].get('material') != 'C1100':
        state['validation_errors'].append('Invalid Copper Grade')
    return state

def check_welding_specs(state: AssemblyState):
    """Verify AWS/ISO welding standard requirements."""
    if 'welding_code' not in state['spec_data']:
        state['validation_errors'].append('Missing welding specification')
    return state

# Compile the graph
workflow = StateGraph(AssemblyState)
workflow.add_node('validate_materials', validate_materials)
workflow.add_node('check_specs', check_welding_specs)
workflow.set_entry_point('validate_materials')
workflow.add_edge('validate_materials', 'check_specs')
workflow.add_edge('check_specs', END)
graph = workflow.compile()
