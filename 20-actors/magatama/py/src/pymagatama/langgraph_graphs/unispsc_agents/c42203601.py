from typing import TypedDict
from langgraph.graph import StateGraph, END

class DefenseSystemState(TypedDict):
    equipment_id: str
    compliance_check: bool
    export_control_status: str

def validate_defense_specs(state: DefenseSystemState):
    # Simulate validation logic for DIN equipment
    print(f'Validating DIN Equipment: {state[\'equipment_id\']}')
    return {'compliance_check': True}

def check_export_regulations(state: DefenseSystemState):
    return {'export_control_status': 'ITAR_COMPLIANT'}

graph = StateGraph(DefenseSystemState)
graph.add_node('validate', validate_defense_specs)
graph.add_node('export', check_export_regulations)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export')
graph.add_edge('export', END)
graph = graph.compile()