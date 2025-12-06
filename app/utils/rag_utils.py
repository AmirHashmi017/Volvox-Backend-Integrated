from langchain_google_genai import ChatGoogleGenerativeAI,GoogleGenerativeAIEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import SystemMessage,HumanMessage,AIMessage
from langchain_classic.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.runnables import RunnableLambda
from dotenv import load_dotenv
from app.database import get_collection,get_gridfs_bucket
from app.config import settings
from bson import ObjectId
from PyPDF2 import PdfReader
from docx import Document as DocxDocument
import csv
import io


async def parse_text_file(file_content: bytes) -> str:
    return file_content.decode('utf-8', errors='ignore')

async def parse_pdf(file_content: bytes) -> str:
    try:
        pdf_file = io.BytesIO(file_content)
        reader = PdfReader(pdf_file)
        text = "\n\n".join([page.extract_text() for page in reader.pages])
        return text
    except ImportError:
        raise ImportError("PyPDF2 is required for PDF parsing. Install: pip install PyPDF2")

async def parse_docx(file_content: bytes) -> str:
    try:
        docx_file = io.BytesIO(file_content)
        doc = DocxDocument(docx_file)
        text = "\n\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text
    except ImportError:
        raise ImportError("python-docx is required for DOCX parsing. Install: pip install python-docx")

async def parse_csv(file_content: bytes) -> str:
    text_content = file_content.decode('utf-8', errors='ignore')
    csv_reader = csv.reader(io.StringIO(text_content))
    rows = [", ".join(row) for row in csv_reader]
    return "\n".join(rows)

async def get_document_content(document_id: str) -> str:
    research_collection = await get_collection(settings.RESEARCH_COLLECTION)
    research_doc = await research_collection.find_one({"_id": ObjectId(document_id)})
    
    if not research_doc:
        raise ValueError(f"Research document with id {document_id} not found")
    
    file_id = research_doc.get("file_id")
    if not file_id:
        raise ValueError(f"No file associated with research document {document_id}")
    
    bucket = await get_gridfs_bucket()
    
    try:
        grid_out = await bucket.open_download_stream(ObjectId(file_id))
    except Exception as e:
        raise ValueError(f"Failed to open file from GridFS: {e}")

    file_content = b""
    while True:
        chunk = await grid_out.read(1024 * 1024) 
        if not chunk:
            break
        file_content += chunk

    extension = research_doc.get("extension", "").lower()
    research_name = research_doc.get("researchName", "Unknown")

    try:
        if extension in ["txt", "md", "py", "js", "json"]:
            content_str = await parse_text_file(file_content)
        elif extension == "pdf":
            content_str = await parse_pdf(file_content)
        elif extension in ["doc", "docx"]:
            content_str = await parse_docx(file_content)
        elif extension == "csv":
            content_str = await parse_csv(file_content)
        else:
            try:
                content_str = file_content.decode('utf-8', errors='ignore')
            except:
                raise ValueError(f"Unsupported file format: {extension}")
    except Exception as e:
        raise ValueError(f"Error parsing {extension} file: {e}")
    
    return content_str

async def get_vector_store_retriever(document_content:str):
    splitter= RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    )
    chunks= splitter.create_documents([document_content])
    embedding = GoogleGenerativeAIEmbeddings(model="text-embedding-004")
    vector_store= FAISS.from_documents(
        documents=chunks,
        embedding=embedding
    )
    retriever= vector_store.as_retriever(
        search_type="similarity", 
        search_kwargs={"k": 4}
    )
    return retriever

def format_docs(retrieved_docs):
    return "\n\n".join(doc.page_content for doc in retrieved_docs)

async def generateResponse(question,chat_id=None,document_id=None):
    load_dotenv()
    context_text = None
    if(document_id):
        document_content= await get_document_content(document_id)
        retriever= await get_vector_store_retriever(document_content)
        context_chain= retriever | RunnableLambda(format_docs)
        context_text= await context_chain.ainvoke(question)

    if context_text:
        system_prompt = f"""
        You are a helpful AI Assistant.
        Use the following context to answer the question:

        CONTEXT:
        {context_text}

        INSTRUCTION:
        - If the question is unrelated to the context, first say:
          "This question is not related to the attached content."
          Then answer normally.
        """
    else:
        system_prompt = "You are a helpful AI assistant."

    chatHistoryModel= await get_collection(settings.CHATHISTORY_COLLECTION)
    chat= await chatHistoryModel.find_one({"_id":ObjectId(chat_id)})
    chat_messages=[SystemMessage(content=system_prompt)]
    if(chat):
        chat_history= chat.get('messages',[])
        for message in chat_history:
            chat_messages.append(HumanMessage(content= message['question']))
            chat_messages.append(AIMessage(content= message['response']))
    
    chat_messages.append(HumanMessage(content=question))

    response=""
    llm= ChatGoogleGenerativeAI(model='gemini-2.5-flash')
    parser= StrOutputParser()
    final_chain= llm | parser
    response= final_chain.invoke(chat_messages)
        
    return response
    

