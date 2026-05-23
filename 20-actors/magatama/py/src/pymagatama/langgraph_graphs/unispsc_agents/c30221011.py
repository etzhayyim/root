from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ZooState(TypedDict):
    facility_id: str
    compliance_status: bool
    tasks: List[str]

def validate_facility(state: ZooState):
    print(f'Validating facility: {state["facility_id"]}')
    return {'compliance_status': True}

def process_husbandry(state: ZooState):
    print('Allocating feed and veterinary resources')
    return {'tasks': ['feed_audit', 'vet_check']}

graph = StateGraph(ZooState)
graph.add_node('validation', validate_facility)
graph.add_node('husbandry', process_husbandry)
graph.add_edge('validation', 'husbandry')
graph.add_edge('husbandry', END)
graph.set_entry_point('validation')
graph = graph.compile()
