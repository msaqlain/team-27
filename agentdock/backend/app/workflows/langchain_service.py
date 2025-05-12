from typing import Optional, Dict, Any
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_groq import ChatGroq
from app.workflows.base_service import ServiceNode
from app.core.config import settings
import os
from dotenv import load_dotenv
import logging

load_dotenv()

class LangChainService(ServiceNode):
    def __init__(
        self,
        service_id: str,
        name: str,
        prompt_template: str,
        input_variables: list[str],
        supervisor_url: str = "http://localhost:8005"
    ):
        super().__init__(service_id, name, supervisor_url)
        self.prompt_template = prompt_template
        self.input_variables = input_variables
        self.logger = logging.getLogger(name)
        
        if not settings.GROQ_API_KEY:
            self.logger.error("GROQ_API_KEY not found in environment variables")
            raise ValueError("GROQ_API_KEY is required. Please set it in the .env file in the root directory.")
            
        self.chain = LLMChain(
            llm=self._get_llm(),
            prompt=PromptTemplate(
                template=prompt_template,
                input_variables=input_variables
            )
        )

    def _get_llm(self):
        """Get the LLM wrapper for Groq"""
        llm = ChatGroq(
            model="llama3-8b-8192",
            api_key=settings.GROQ_API_KEY,
            temperature=0.1
        )
        self.logger.info("Initialized Groq LLM with llama3-8b-8192")
        return llm

    async def execute(self, context: Optional[Dict[str, Any]] = None):
        """Execute the LangChain processing"""
        if not context:
            raise ValueError("Context is required for LangChain processing")

        # Extract required variables from context
        inputs = {var: context.get(var) for var in self.input_variables}
        
        # Log the execution
        self.logger.info("Executing with Groq LLM")
        self.logger.info(f"Input variables: {inputs}")
        
        # Run the chain
        result = await self.chain.arun(**inputs)
        
        # Log the result
        self.logger.info("LLM Response received from Groq")
        
        # Store the result in context for other services
        context["result"] = result
        return result 