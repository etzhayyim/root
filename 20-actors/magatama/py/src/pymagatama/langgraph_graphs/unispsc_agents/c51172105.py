from typing import TypedDict
from langgraph.graph import StateGraph, END

class ChemicalProcurementState(TypedDict):
    material_name: str
    purity_level: float
    safety_check_passed: bool

def validate_compliance(state: ChemicalProcurementState):
    print(f'Validating storage specs for {state['material_name']}')
    return {'safety_check_passed': state['purity_level'] >= 98.0}

def update_inventory(state: ChemicalProcurementState):
    print('Logging batch to hazardous inventory system.')
    return {'safety_check_passed': True}

graph = StateGraph(ChemicalProcurementState)
graph.add_node('validate', validate_compliance)
graph.add_node('log', update_inventory)
graph.set_entry_point('validate')
graph.add_edge('validate', 'log')
graph.add_edge('log', END)
graph = graph.compile()