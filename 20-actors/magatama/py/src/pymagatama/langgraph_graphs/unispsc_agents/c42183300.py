from typing import TypedDict
from langgraph.graph import StateGraph, END

class ENTUnitState(TypedDict):
    part_number: str
    compliance_checked: bool
    needs_sterilization: bool

def validate_part(state: ENTUnitState) -> ENTUnitState:
    print(f'Validating medical part: {state["part_number"]}')
    state['compliance_checked'] = True
    return state

def check_sterilization(state: ENTUnitState) -> ENTUnitState:
    if state.get('needs_sterilization', False):
        print('Verification: Sterilization protocol required.')
    return state

graph = StateGraph(ENTUnitState)
graph.add_node('validate', validate_part)
graph.add_node('sterilization', check_sterilization)
graph.set_entry_point('validate')
graph.add_edge('validate', 'sterilization')
graph.add_edge('sterilization', END)
graph = graph.compile()