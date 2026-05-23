from typing import TypedDict
from langgraph.graph import StateGraph, END

class HardwareState(TypedDict):
    specs: dict
    validated: bool

def validate_specs(state: HardwareState):
    required = ['material', 'dimensions', 'compliance_doc']
    all_present = all(k in state['specs'] for k in required)
    return {'validated': all_present}

def process_procurement(state: HardwareState):
    print('Processing hardware order for metallic components...')
    return {'validated': True}

graph = StateGraph(HardwareState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()
