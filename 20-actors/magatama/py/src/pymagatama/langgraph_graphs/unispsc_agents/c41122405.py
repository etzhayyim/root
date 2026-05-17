from typing import TypedDict
from langgraph.graph import StateGraph, END

class LabForcepsState(TypedDict):
    spec_data: dict
    is_validated: bool
    validation_report: str

def validate_specs(state: LabForcepsState):
    required = ['material_grade', 'autoclave_compatibility']
    missing = [f for f in required if f not in state['spec_data']]
    if missing:
        return {'is_validated': False, 'validation_report': f'Missing: {missing}'}
    return {'is_validated': True, 'validation_report': 'Specs validated'}

def process_forceps(state: LabForcepsState):
    return {'validation_report': 'Processing ready for procurement'}

graph = StateGraph(LabForcepsState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_forceps)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()