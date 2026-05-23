from typing import TypedDict
from langgraph.graph import StateGraph, END

class CraniotomyState(TypedDict):
    instrument_list: list
    is_sterile: bool
    compliance_checked: bool

def validate_instruments(state: CraniotomyState):
    state['compliance_checked'] = all('ISO-13485' in item for item in state['instrument_list'])
    print('Validating craniotomy kit compliance...')
    return {'compliance_checked': state['compliance_checked']}

def verify_sterility(state: CraniotomyState):
    state['is_sterile'] = True
    return {'is_sterile': True}

graph = StateGraph(CraniotomyState)
graph.add_node('validate', validate_instruments)
graph.add_node('sterility', verify_sterility)
graph.set_entry_point('validate')
graph.add_edge('validate', 'sterility')
graph.add_edge('sterility', END)
graph = graph.compile()
