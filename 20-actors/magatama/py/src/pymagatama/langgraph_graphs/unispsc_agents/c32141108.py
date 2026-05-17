from typing import TypedDict
from langgraph.graph import StateGraph, END

class ElectrodeState(TypedDict):
    specs: dict
    validation_passed: bool

def validate_specs(state: ElectrodeState):
    required = ['material_composition', 'dimensional_tolerance_mm']
    valid = all(key in state['specs'] for key in required)
    return {'validation_passed': valid}

def process_procurement(state: ElectrodeState):
    return {'validation_passed': True}

graph = StateGraph(ElectrodeState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_procurement)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
graph.compile()