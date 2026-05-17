from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class EquipmentState(TypedDict):
    equipment_id: str
    specs: dict
    is_compliant: bool
    validation_log: List[str]

def validate_specs(state: EquipmentState):
    required_keys = ['Engine Power', 'Safety Certification']
    logs = []
    compliant = True
    for key in required_keys:
        if key not in state['specs']:
            logs.append(f'Missing field: {key}')
            compliant = False
    return {'is_compliant': compliant, 'validation_log': logs}

workflow = StateGraph(EquipmentState)
workflow.add_node('validation', validate_specs)
workflow.set_entry_point('validation')
workflow.add_edge('validation', END)
graph = workflow.compile()