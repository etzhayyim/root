from typing import TypedDict
from langgraph.graph import StateGraph, END

class SteelAssemblyState(TypedDict):
    spec_data: dict
    validation_status: str
    compliance_report: str

def validate_material(state: SteelAssemblyState):
    # Industry specific logic for carbon steel welding validation
    is_valid = state['spec_data'].get('grade') in ['SS400', 'S235JR']
    return {'validation_status': 'COMPLIANT' if is_valid else 'FAILED'}

def generate_report(state: SteelAssemblyState):
    report = f'Assembly validation complete: {state[\"validation_status\"]}'
    return {'compliance_report': report}

graph = StateGraph(SteelAssemblyState)
graph.add_node('validate', validate_material)
graph.add_node('report', generate_report)
graph.set_entry_point('validate')
graph.add_edge('validate', 'report')
graph.add_edge('report', END)
graph = graph.compile()