from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.core.config import settings
import structlog

logger = structlog.get_logger(__name__)

class DocumentQAAgent:
    def __init__(self):
        # We use ChatOpenAI because LiteLLM provides an OpenAI-compatible API
        self.llm = ChatOpenAI(
            openai_api_base=settings.LITELLM_API_BASE,
            openai_api_key="sk-litellm", # API key is managed by LiteLLM if needed
            model_name=settings.DEFAULT_MODEL,
            temperature=0.0
        )
        
        self.qa_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert sales assistant. You extract structured data (like BANT - Budget, Authority, Need, Timeline) and answer questions strictly based on the provided document text. Do not invent information."),
            ("user", "Document Text:\n{document_text}\n\nQuestion: {question}")
        ])
        
        self.chain = self.qa_prompt | self.llm
        
    async def answer_question(self, document_text: str, question: str) -> str:
        logger.info("Executing Document QA", question_length=len(question), doc_length=len(document_text))
        response = await self.chain.ainvoke({
            "document_text": document_text,
            "question": question
        })
        return response.content
