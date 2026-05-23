from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class EquipmentState(TypedDict):
    specifications: dict
    is_compliant: bool
    validation_log: List[str]

def validate_specs(state: EquipmentState):
    log = []
    compliant = True
    if state['specifications'].get('power_rating', 0) <= 0:
        log.append('Invalid power rating')
        compliant = False
    return {'is_compliant': compliant, 'validation_log': log}

graph = StateGraph(EquipmentState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
