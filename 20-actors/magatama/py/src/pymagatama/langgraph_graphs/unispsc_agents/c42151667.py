from typing import TypedDict
from langgraph.graph import StateGraph, END

class DentalState(TypedDict):
    product_id: str
    compliance_passed: bool
    is_sterile: bool

def validate_material(state: DentalState):
    print(f'Validating material specifications for {state['product_id']}')
    return {'compliance_passed': True}

def check_sterility(state: DentalState):
    print('Verifying sterilization documentation...')
    return {'is_sterile': True}

graph = StateGraph(DentalState)
graph.add_node('validate_material', validate_material)
graph.add_node('check_sterility', check_sterility)
graph.add_edge('validate_material', 'check_sterility')
graph.add_edge('check_sterility', END)
graph.set_entry_point('validate_material')
graph = graph.compile()
