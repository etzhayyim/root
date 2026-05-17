from typing import TypedDict
from langgraph.graph import StateGraph, END

class RotisserieState(TypedDict):
    spec_data: dict
    validation_passed: bool

def validate_specs(state: RotisserieState):
    required = ['Voltage', 'NSF_Certification']
    return {'validation_passed': all(k in state['spec_data'] for k in required)}

def route_by_validation(state: RotisserieState):
    return 'process' if state['validation_passed'] else END

def process_order(state: RotisserieState):
    print('Proceeding with procurement workflow for validated rotisserie unit.')
    return state

graph = StateGraph(RotisserieState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_order)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_validation)
graph.add_edge('process', END)
compile_graph = graph.compile()