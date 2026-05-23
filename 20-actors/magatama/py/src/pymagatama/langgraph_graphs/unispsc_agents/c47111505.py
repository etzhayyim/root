from typing import TypedDict
from langgraph.graph import StateGraph, END

class EquipmentState(TypedDict):
    load_capacity: float
    material: str
    is_compliant: bool

def validate_load_specs(state: EquipmentState):
    if state['load_capacity'] > 200:
        return {'is_compliant': True}
    return {'is_compliant': False}

def update_status(state: EquipmentState):
    # Simulate procurement workflow completion
    return {'is_compliant': True}

graph = StateGraph(EquipmentState)
graph.add_node('validate', validate_load_specs)
graph.add_node('finalize', update_status)
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph.set_entry_point('validate')
compiled_graph = graph.compile()
