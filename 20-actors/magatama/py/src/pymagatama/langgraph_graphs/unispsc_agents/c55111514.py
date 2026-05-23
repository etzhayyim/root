from typing import TypedDict
from langgraph.graph import StateGraph, END

class DVDProcurementState(TypedDict):
    title: str
    region_code: str
    is_licensed: bool
    validation_status: str

def validate_license(state: DVDProcurementState):
    state['validation_status'] = 'verified' if state['is_licensed'] else 'rejected'
    return state

def check_region(state: DVDProcurementState):
    if state['region_code'] != 'All':
        print(f'Warning: Region restriction detected for {state['title']}')
    return state

graph = StateGraph(DVDProcurementState)
graph.add_node('validate_license', validate_license)
graph.add_node('check_region', check_region)
graph.set_entry_point('validate_license')
graph.add_edge('validate_license', 'check_region')
graph.add_edge('check_region', END)
graph = graph.compile()
