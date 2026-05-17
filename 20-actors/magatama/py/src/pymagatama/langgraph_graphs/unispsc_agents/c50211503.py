from typing import TypedDict
from langgraph.graph import StateGraph, END

class TobaccoState(TypedDict):
    moisture_level: float
    compliance_cleared: bool
    origin: str

def validate_moisture(state: TobaccoState):
    if 10.0 <= state['moisture_level'] <= 15.0:
        return {'compliance_cleared': True}
    return {'compliance_cleared': False}

def check_origin_regulations(state: TobaccoState):
    print(f'Checking import regulations for: {state.get('origin')}')
    return {'compliance_cleared': True}

graph = StateGraph(TobaccoState)
graph.add_node('validate_moisture', validate_moisture)
graph.add_node('check_origin', check_origin_regulations)
graph.set_entry_point('validate_moisture')
graph.add_edge('validate_moisture', 'check_origin')
graph.add_edge('check_origin', END)
graph = graph.compile()