from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_groq import ChatGroq
from typing import Dict, Optional
import json
import logging

logger = logging.getLogger(__name__)

class LangChainService:
    def __init__(self, groq_api_key: str):
        """Initialize LangChain service with Groq LLM"""
        self.llm = ChatGroq(
            model="llama3-8b-8192",
            api_key=groq_api_key,
            temperature=0.1
        )
        
        # Initialize analyzers for different MCP types
        self.github_analyzer = self._create_analyzer("GitHub")
        self.slack_analyzer = self._create_analyzer("Slack")
        self.jira_analyzer = self._create_analyzer("Jira")
        
        # Initialize intent classifier
        self.intent_classifier = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate(
                template="""You are an intent classifier for a chatbot that handles GitHub, Slack, and Jira operations. 
                Analyze this message: "{message}"
                
                Return a JSON object with:
                1. "platform": Either "github", "slack", "jira", "both", or "conversation" (for general chat)
                2. "confidence": A number between 0 and 1 indicating your confidence
                
                If platform is "github" or "both", include these fields for GitHub:
                - github_action: one of [list_prs, get_pr_summary, get_stats, create_pr, list_my_repos]
                - owner: repository owner (if mentioned)
                - repo: repository name (if mentioned)
                - pr_number: pull request number (if mentioned)
                
                If platform is "slack" or "both", include these fields for Slack:
                - slack_action: one of [list_channels, send_message, get_conversation_history]
                - channel: channel name or ID (if mentioned)
                - message_content: content of message to send (if applicable)
                - time_range: time range for history (if applicable)
                
                If platform is "jira" or "both", include these fields for Jira:
                - jira_action: one of [list_issues, get_issue_details, get_sprint_status, get_team_velocity]
                - project: project key (if mentioned)
                - issue_key: issue key (if mentioned)
                - sprint: sprint name or ID (if mentioned)
                - status: issue status (if mentioned)
                
                Return ONLY the JSON object, no other text.""",
                input_variables=["message"]
            )
        )

    def _create_analyzer(self, mcp_type: str) -> LLMChain:
        """Create an analyzer chain for a specific MCP type"""
        templates = {
            "GitHub": """Analyze the following GitHub data:
                {data}
                
                Provide a comprehensive analysis that includes:
                1. Repository health and activity metrics
                2. Pull request trends and patterns
                3. Code review and collaboration insights
                4. Recommendations for improvement
                
                Analysis:""",
            "Slack": """Analyze the following Slack data:
                {data}
                
                Provide a comprehensive analysis that includes:
                1. Channel activity and engagement metrics
                2. Communication patterns and trends
                3. Team collaboration insights
                4. Recommendations for improvement
                
                Analysis:""",
            "Jira": """Analyze the following Jira data:
                {data}
                
                Provide a comprehensive analysis that includes:
                1. Project progress and velocity metrics
                2. Sprint performance and burndown trends
                3. Issue resolution patterns and bottlenecks
                4. Recommendations for improvement
                
                Analysis:"""
        }
        
        return LLMChain(
            llm=self.llm,
            prompt=PromptTemplate(
                template=templates.get(mcp_type, """Analyze the following {mcp_type} data:
                {data}
                
                Provide a comprehensive analysis that includes:
                1. Key metrics and trends
                2. Notable patterns or anomalies
                3. Potential issues or concerns
                4. Recommendations for improvement
                
                Analysis:"""),
                input_variables=["mcp_type", "data"]
            )
        )

    async def analyze_mcp_data(self, mcp_type: str, data: Dict) -> str:
        """Analyze MCP data using the appropriate analyzer"""
        try:
            analyzer = getattr(self, f"{mcp_type.lower()}_analyzer")
            result = await analyzer.arun(
                mcp_type=mcp_type,
                data=json.dumps(data, indent=2)
            )
            logger.info(f"Successfully analyzed {mcp_type} data")
            return result
        except Exception as e:
            logger.error(f"Error analyzing {mcp_type} data: {str(e)}")
            return f"Error analyzing {mcp_type} data: {str(e)}"

    async def determine_intent(self, message: str) -> Dict:
        """Determine the intent of a user message"""
        try:
            result = await self.intent_classifier.arun(message=message)
            return json.loads(result)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse intent classifier response: {e}")
            return {"platform": "conversation"}
        except Exception as e:
            logger.error(f"Error in determine_intent: {str(e)}")
            return {"platform": "conversation"}

    async def generate_response(self, message: str, analyses: Dict[str, str]) -> str:
        """Generate a response based on the message and analyses"""
        try:
            completion = await self.llm.agenerate(
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that analyzes team productivity and collaboration across GitHub, Slack, and Jira."},
                    {"role": "user", "content": message},
                    *[{"role": "assistant", "content": f"{platform} Analysis: {analysis}"} 
                      for platform, analysis in analyses.items()]
                ]
            )
            return completion.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return "I apologize, but I encountered an error while generating a response." 