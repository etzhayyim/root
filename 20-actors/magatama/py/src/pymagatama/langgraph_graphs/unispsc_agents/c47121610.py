from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CleaningMachineState(TypedDict):
    model_id: str
    specs: dict
    validation_passed: bool
    maintenance_plan: str

def validate_specs(state: CleaningMachineState):
    # Business logic for floor machine specs validation
    required_keys = ['scrub_width', 'battery_life']
    passed = all(k in state['specs'] for k in required_keys)
    return {'validation_passed': passed}

def assign_maintenance(state: CleaningMachineState):
    return {'maintenance_plan': 'Standard 12-month SLA'}

graph = StateGraph(CleaningMachineState)
graph.add_node('validate', validate_specs)
graph.add_node('maintenance', assign_maintenance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'maintenance')
graph.add_edge('maintenance', END)
graph = graph.compile()
