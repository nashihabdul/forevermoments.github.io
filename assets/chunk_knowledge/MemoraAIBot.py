import os
import telebot
import gradio as gr
import random
import time
from langchain_community.llms import Ollama
from langchain_nomic import NomicEmbeddings
from langchain_chroma import Chroma
import cohere
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder 
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
import cohere
from FlagEmbedding import BGEM3FlagModel
from langchain_ollama import ChatOllama

class BGEWrapper:
    def __init__(self, model_name_or_path='BAAI/bge-m3', device='cuda', use_fp16=True):
        self.model = BGEM3FlagModel(
            model_name_or_path=model_name_or_path,
            use_fp16=use_fp16,
            device=device
        )

    def embed_documents(self, texts):
        outputs = self.model.encode(
            texts,
            return_dense=True,
            return_sparse=False
        )

        # outputs adalah dict → kita ambil 'dense_vecs'
        dense_vecs = outputs['dense_vecs']  # Ini harus list atau np.array
        return [vec.tolist() if hasattr(vec, "tolist") else vec for vec in dense_vecs]

    def embed_query(self, text):
        outputs = self.model.encode(
            [text],
            return_dense=True,
            return_sparse=False
        )

        dense_vecs = outputs['dense_vecs']
        vec = dense_vecs[0]
        return vec.tolist() if hasattr(vec, "tolist") else vec
    
# Fungsi untuk mendapatkan embedding function berdasarkan parameter
def get_embedding_function(model_name='nomic', device='cuda'):
    if model_name == 'nomic':
        return NomicEmbeddings(
            model='nomic-embed-text-v1.5',
            inference_mode='local',
            device=device,
        )
    elif model_name == 'bge-m3':
        return BGEWrapper(model_name_or_path='BAAI/bge-m3', device=device)
    else:
        raise ValueError(f"Model '{model_name}' tidak dikenal. Pilih 'nomic' atau 'bge-m3'.")
    
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

def contextualized_question(input: dict):
    if input.get("chat_history"):
        return contextualize_q_chain
    else:
        return input["question"]
    
def rerank_relevance(reformulated_question,list_document):
    response_rerank = co.rerank(
                                model="rerank-multilingual-v3.0",
                                query=reformulated_question,
                                documents=list_document,
                                return_documents=True
                            )
    return [i.document.text for i in response_rerank.results[0:15] ]

def get_llm_response(history):
    print("=== [DEBUG] HISTORY ===")
    print(history)

    latest_question = history[-1]['content']
    print("=== [DEBUG] LATEST QUESTION ===")
    print(latest_question)

    reformulated_question = contextualize_q_chain.invoke({
        "chat_history": history,
        "question": latest_question
    })
    print("=== [DEBUG] REFORMULATED QUESTION ===")
    print(reformulated_question)

    retrieved_documents = retriever.get_relevant_documents(reformulated_question)
    print("=== [DEBUG] RETRIEVED DOCUMENTS ===")
    for i, doc in enumerate(retrieved_documents):
        print(f"[{i}] {doc.page_content[:200]}...")  # print sebagian saja

    context_string = "\n\n".join([i.page_content for i in retrieved_documents])
    print("=== [DEBUG] CONTEXT STRING ===")
    print(context_string[:1000])  # print hanya 1000 karakter pertama

    # Membungkus context dalam HumanMessage atau AIMessage
    context_message = [HumanMessage(content=context_string)]
    print("=== [DEBUG] CONTEXT MESSAGE ===")
    print(context_message)

    try:
        response = prompt_context_question.invoke({
            "context": context_message,  # List of HumanMessage, bukan string biasa
            "question": reformulated_question
        })
        print("=== [DEBUG] RAW RESPONSE ===")
        print(response)
    except Exception as e:
        print("=== [ERROR] EXCEPTION SAAT INVOKE PROMPT ===")
        print(str(e))
        raise e

    if isinstance(response, dict):
        return response.get("text") or response.get("content") or str(response)
    return str(response)

def test1(question):
    response = prompt_context_question.invoke({"context":[],"question":question})
    return response

CHROMA_PATH = "/em-data/jupyter/nashih/Agent/UploadDocument/attachment/testing/knowledge/2"

embedding_function = get_embedding_function(model_name='bge-m3', device='cuda')

db = Chroma(
    collection_name="forever_moments",
    persist_directory=CHROMA_PATH, 
    embedding_function=embedding_function
)

co = cohere.Client("Bj0lFx0ZryIDA6PTnSIHvE5filfO2kxcF7UTtKBK")

# Konfigurasi LLM
llm = ChatOllama(model="qwen2.5", temperature=0.2, num_ctx=6000)

retriever = db.as_retriever(
    search_type = "similarity",
    search_kwargs = {"k":5}
)

contextualize_q_system_prompt = """Given a chat history and the latest user question \
which might reference context in the chat history, formulate a standalone question \
which can be understood without the chat history. Do NOT answer the question, \
just reformulate it if needed and otherwise return it as is."""

contextualize_q_prompt= ChatPromptTemplate.from_messages(
    [
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{question}"),
    ]
)


contextualize_q_chain = contextualize_q_prompt | llm | StrOutputParser()

qa_system_prompt = """You are an assistant for question-answering tasks. \
                    Use the following pieces of retrieved context to answer the question. \
                    Always answer in English. \
                    If you don't know the answer, just say that you don't know. \
                    Use three sentences maximum and keep the answer concise.\
                    If you cant give the direct answer, Please give a direct answer instead of beating around the bush and then answering the question.\

                    {context}"""

qa_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", qa_system_prompt),
        MessagesPlaceholder(variable_name="context"),
        ("human", "{question}"),
    ]
)

prompt_context_question = qa_prompt | llm | StrOutputParser()

BOT_TOKEN = '7571209477:AAFteZX-kStVN47UFG3rAarnch_bXjhaY0c'

bot = telebot.TeleBot(BOT_TOKEN)

global history
history = []

@bot.message_handler(commands=['hello','hi'])
def send_welcome(message):
    bot.reply_to(message, "Hi how can i help you?")


def reset(message, history):
    history.clear()
    return []


@bot.message_handler(func=lambda msg: True)
def echo_all(message):
    global history
    question = message.text
    if question =="/reset":
        history_reset = reset(message,history)
        history = history_reset
        response_bot = "Knowledge Restart"

    else :
        print(question)
        history.append({'role':'user', 'content': question})
        response_bot =get_llm_response(history)
        history.append({'role':'user', 'content': response_bot})
    print(history)
    bot.reply_to(message, response_bot)

bot.infinity_polling()