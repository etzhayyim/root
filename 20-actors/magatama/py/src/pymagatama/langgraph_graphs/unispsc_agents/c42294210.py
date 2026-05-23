from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SurgicalState(TypedDict):
    instrument_list: List[str]
    compliance_checked: bool
    sterilization_verified: bool

def validate_instruments(state: SurgicalState):
    state['compliance_checked'] = all('ISO' in item for item in state['instrument_list'])
    print('Validating medical device compliance...')
    return state

def verify_sterilization(state: SurgicalState):
    state['sterilization_verified'] = True
    print('Verifying sterile packaging standards...')
    return state

graph = StateGraph(SurgicalState)
graph.add_node('validate', validate_instruments)
graph.add_node('sterilize', verify_sterilization)
graph.add_edge('validate', 'sterilize')
graph.add_edge('sterilize', END)
graph.set_entry_point('validate')
graph = graph.compile()
