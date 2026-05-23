from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ChemicalState(TypedDict):
    purity: float
    cas_compliant: bool
    storage_temp: str
    validation_passed: bool

def validate_chemistry(state: ChemicalState):
    passed = state['purity'] >= 0.99 and state['cas_compliant']
    return {'validation_passed': passed}

def check_storage(state: ChemicalState):
    print(f'Checking storage requirement: {state['storage_temp']}')
    return {}

graph = StateGraph(ChemicalState)
graph.add_node('validate', validate_chemistry)
graph.add_node('storage', check_storage)
graph.add_edge('validate', 'storage')
graph.add_edge('storage', END)
graph.set_entry_point('validate')
graph = graph.compile()
