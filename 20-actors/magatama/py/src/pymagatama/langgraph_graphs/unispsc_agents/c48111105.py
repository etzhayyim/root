from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class MachineState(TypedDict):
    machine_id: str
    specs: dict
    validation_passed: bool

def validate_specs(state: MachineState):
    required = ['refrigerant_type', 'cooling_capacity_kw']
    passed = all(k in state['specs'] for k in required)
    return {'validation_passed': passed}

def approval_step(state: MachineState):
    print(f'Finalizing procurement for {state['machine_id']}')
    return {'validation_passed': True}

graph = StateGraph(MachineState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_step)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()