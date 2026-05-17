from typing import TypedDict
from langgraph.graph import StateGraph, END

class OilTestState(TypedDict):
    kit_id: str
    validation_status: str
    compliance_check: bool

def validate_kit(state: OilTestState):
    print(f'Validating kit: {state['kit_id']}')
    return {'validation_status': 'verified', 'compliance_check': True}

def check_sds(state: OilTestState):
    print('Verifying chemical safety data sheets...')
    return {'compliance_check': True}

graph = StateGraph(OilTestState)
graph.add_node('validate', validate_kit)
graph.add_node('safety', check_sds)
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph.set_entry_point('validate')
graph = graph.compile()