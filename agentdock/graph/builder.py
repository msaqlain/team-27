from state import State
from langgraph.graph import StateGraph, START, END
from nodes import (supervisorNode, githubNode, jiraNode, slackNode, finalNode)
from conditional_edges import agent_selector



workflow = StateGraph(State)
workflow.add_node("supervisor_node", supervisorNode)
workflow.add_node("github_agent_node", githubNode)
workflow.add_node("slack_agent_node", slackNode)
workflow.add_node("jira_agent_node", jiraNode)
workflow.add_node("final_node", finalNode)


workflow.add_edge(START, "supervisor_node")
workflow.add_conditional_edges("supervisor_node", agent_selector)
workflow.add_conditional_edges("github_agent_node", agent_selector)
workflow.add_conditional_edges("slack_agent_node", agent_selector)
workflow.add_conditional_edges("jira_agent_node", agent_selector)

workflow.add_edge("final_node", END)

graph_builder = workflow.compile()
