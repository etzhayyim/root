from typing import TypedDict
from langgraph.graph import StateGraph, END

class CopperAssemblyState(TypedDict):
    spec_sheet: dict
    validation_passed: bool
    error_log: list

def validate_specs(state: CopperAssemblyState):
    specs = state['spec_sheet']
    passed = specs.get('conductivity', 0) >= 95 and 'material' in specs
    return {'validation_passed': passed}

def process_assembly(state: CopperAssemblyState):
    return {'error_log': ['Compliance check completed']}

graph = StateGraph(CopperAssemblyState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_assembly)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
graph = graph.compile()