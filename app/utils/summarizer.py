from .rag_utils import get_document_content,get_vector_store_retriever,format_docs
from youtube_transcript_api import YouTubeTranscriptApi
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from dotenv import load_dotenv
from typing import List
import re

load_dotenv()

def extract_video_id(url):
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/v\/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com\/watch\?.*v=([a-zA-Z0-9_-]{11})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    if re.match(r'^[a-zA-Z0-9_-]{11}$', url):
        return url
    
    raise ValueError("Invalid YouTube URL or Video ID")

async def SummarizeResearch(documents:List[str]):
    try:
        content_to_summarize=""
        for document in documents:
            document_content= await get_document_content(document)
            content_to_summarize+=document_content

        prompt= PromptTemplate(
        template="""
        You are a helpful AI Assistant summarize this {content}
        """,
        input_variables=['content']
        )
        llm= ChatGoogleGenerativeAI(model='gemini-2.5-flash')
        parser= StrOutputParser()
        summarize_chain= prompt | llm | parser

        result= await summarize_chain.ainvoke(content_to_summarize)
        return result
    except Exception as e:
        return str(e)

async def SummarizeVideo(video_url:str):
    try:
        question= 'Summarize this Content of video'
        video_id = extract_video_id(video_url)
        transcript_list = YouTubeTranscriptApi().fetch(video_id)
        transcript = " ".join([item.text for item in transcript_list.snippets])
        retriever= await get_vector_store_retriever(transcript)
        prompt= PromptTemplate(
            template="""
            You are a helpful AI Assistant summarize this {content} of video. The content can 
            be irrelevant to each other becaus emay it's different documents but you have to cover 
            all the aspects.
            """,
            input_variables=['content']
        )
        llm= ChatGoogleGenerativeAI(model='gemini-2.5-flash')
        parser= StrOutputParser()
        video_summarize_chain= retriever | RunnableLambda(format_docs) | prompt | llm | parser
        result= await video_summarize_chain.ainvoke(question)
        return result

    except Exception as e:
        return str(e)