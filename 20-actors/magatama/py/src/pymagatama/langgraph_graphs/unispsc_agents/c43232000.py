from typing import TypedDict, Annotated; import operator; from langgraph.graph import StateGraph, END; class GameSoftwareState(TypedDict):
    software_id: str
    compliance_check: bool
    license_validated: bool
    final_report: str; def validate_license(state: GameSoftwareState):
    return {'license_validated': True}; def verify_compliance(state: GameSoftwareState):
    return {'compliance_check': True}; graph = StateGraph(GameSoftwareState); graph.add_node('validate', validate_license); graph.add_node('compliance', verify_compliance); graph.add_edge('validate', 'compliance'); graph.add_edge('compliance', END); graph.set_entry_point('validate'); graph = graph.compile()