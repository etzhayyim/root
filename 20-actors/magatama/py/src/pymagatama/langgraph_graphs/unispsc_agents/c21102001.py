from typing import TypedDict
from langgraph.graph import StateGraph, END

class IrrigationState(TypedDict):
    spec_data: dict
    validation_log: list

def validate_specs(state: IrrigationState):
    # Business logic for irrigation hardware compliance
    required = ['Flow Rate', 'Operating Pressure']
    logs = [key for key in required if key not in state['spec_data']]
    return {'validation_log': logs}

graph = StateGraph(IrrigationState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
