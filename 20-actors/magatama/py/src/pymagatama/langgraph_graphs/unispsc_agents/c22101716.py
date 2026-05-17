from typing import TypedDict
from langgraph.graph import StateGraph, END

class CuttingMachineState(TypedDict):
    specs: dict
    validation_result: bool
    compliance_flag: bool

def validate_specs(state: CuttingMachineState):
    power = state['specs'].get('power', 0)
    return {'validation_result': power > 0}

def check_compliance(state: CuttingMachineState):
    return {'compliance_flag': state['validation_result']}

graph = StateGraph(CuttingMachineState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()