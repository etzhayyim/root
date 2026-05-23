from typing import TypedDict
from langgraph.graph import StateGraph, END

class ToxicologyState(TypedDict):
    item_name: str
    compliance_checked: bool
    safety_path: str

def validate_safety_data(state: ToxicologyState):
    print(f'Validating MSDS for {state["item_name"]}...')
    return {'compliance_checked': True}

def process_procurement(state: ToxicologyState):
    print('Initiating toxicology supply purchase workflow.')
    return {'safety_path': 'high_security_storage'}

graph = StateGraph(ToxicologyState)
graph.add_node('validate', validate_safety_data)
graph.add_node('process', process_procurement)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
