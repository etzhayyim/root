from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class EmergencySupplyState(TypedDict):
    item_name: str
    specs: dict
    is_compliant: bool
    validation_log: List[str]

def validate_specs(state: EmergencySupplyState):
    log = []
    compliant = True
    required = ['thermal_rating', 'material_quality']
    for field in required:
        if field not in state['specs']:
            log.append(f'Missing spec: {field}')
            compliant = False
    return {'is_compliant': compliant, 'validation_log': log}

graph = StateGraph(EmergencySupplyState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()