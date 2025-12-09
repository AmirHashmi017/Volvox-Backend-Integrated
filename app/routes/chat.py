from fastapi import APIRouter, HTTPException, status, Depends, File, Form, Query
from fastapi.responses import StreamingResponse
from app.utils.rag_utils import generateResponse
from app.utils.summarizer import SummarizeResearch, SummarizeVideo, SummarizeTextResearch

from app.models.chatHistory import Message

from app.database import get_collection
from app.config import settings
from datetime import datetime, timezone
from bson import ObjectId
from typing import List, AsyncGenerator, Optional
import mimetypes
from pathlib import Path
from pydantic import BaseModel

class SummarizeBody(BaseModel):
    documents: list[str]

class SummarizeTextBody(BaseModel):
    content: str

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post('/ask', response_model=dict, status_code=status.HTTP_200_OK)
async def askLLM(
    user_id: str = Query(..., alias="user_id"),
    question: str= Query(...),
    chat_id: Optional[str]= Query(None),
    document_id: Optional[str]= Query(None),
    web_search: Optional[bool]= False
):
    response= await generateResponse(question,chat_id,document_id,web_search)
    chatHistory= await get_collection(settings.CHATHISTORY_COLLECTION)
    new_message = Message(
        question=question,
        response=response,
        research_id=document_id,             
    )
    if chat_id:
        chat_doc = await chatHistory.find_one({"_id": ObjectId(chat_id),"user_id":user_id})
        if not chat_doc:
            raise HTTPException(
                status_code=404,
                detail=f"Chat with id '{chat_id}' not found",
            )

        await chatHistory.update_one(
            {"_id": ObjectId(chat_id)},
            {
                "$push": {"messages": new_message.dict(by_alias=True)},
            },
        )
        final_chat_id = chat_id
        title= chat_doc.get("title")
    else:
        title= question[:50]
        insert_result = await chatHistory.insert_one({
            "user_id": user_id,
            "title": title,
            "messages": [new_message.dict(by_alias=True)],
            "createdAt": datetime.now(timezone.utc)
            }
        )
        final_chat_id= str(insert_result.inserted_id)
    
    return {
        "response": response,
        "chat_id": final_chat_id,
        "chat_title": title
    }

@router.get('/chatHistory',response_model=List[dict],status_code=status.HTTP_200_OK)
async def getChatHistory(
    user_id: str = Query(..., alias="user_id"),
):
    chatHistoryModel= await get_collection(settings.CHATHISTORY_COLLECTION)
    chats_cursor = chatHistoryModel.find({"user_id": user_id}, 
                                         {"title": 1, "createdAt": 1}).sort("createdAt", -1) 

    chats=[]
    async for chat in chats_cursor:
        chats.append(
            {
                "chat_id": str(chat["_id"]),
                "chat_title": chat.get("title"),
            "createdAt": chat.get("createdAt")
            }
        )
    
    return chats

@router.get('/chatHistory/{chat_id}',response_model=dict,status_code=status.HTTP_200_OK)
async def getChatHistory(
    chat_id: str,
    user_id: str = Query(..., alias="user_id"),
):
    chatHistoryModel= await get_collection(settings.CHATHISTORY_COLLECTION)
    chat = await chatHistoryModel.find_one({"_id":ObjectId(chat_id),
                                            "user_id": user_id})

    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    return{
        "chat_id": chat_id,
        "chat_title": chat.get("title"),
        "messages": chat.get("messages",[])
    }

@router.delete('/deleteChat/{chat_id}',response_model=str, status_code=status.HTTP_200_OK)
async def deleteChat(
    chat_id:str,
    user_id: str = Query(..., alias="user_id"),
):
    chatHistoryModel= await get_collection(settings.CHATHISTORY_COLLECTION)
    chat= await chatHistoryModel.find_one({"_id":ObjectId(chat_id),
                                           "user_id":user_id})
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    await chatHistoryModel.delete_one({"_id":ObjectId(chat_id),
                                           "user_id":user_id})
    return "Chat Deleted Successfully"

@router.post('/summarize-research',response_model=str,status_code=status.HTTP_200_OK)
async def summarizeResearch(
        body: SummarizeBody
        ):
    summary= await SummarizeResearch(body.documents)
    return summary

@router.post('/summarize-research-text',response_model=str,status_code=status.HTTP_200_OK)
async def summarizeResearch(
        body: SummarizeTextBody
        ):
    summary= await SummarizeTextResearch(body.content)
    return summary

@router.post('/summarize-video',response_model=str,status_code=status.HTTP_200_OK)
async def summarizeVideo(
        video_url: str
    ):
    summary= await SummarizeVideo(video_url)
    return summary
    
    
