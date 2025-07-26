from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_ollama import OllamaLLM

# Embeddings
embedding_model = HuggingFaceEmbeddings(
    model_name="intfloat/e5-small",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True}
)

# Load FAISS vectorstore safely
vectorstore = FAISS.load_local(
    "faiss_index",
    embeddings=embedding_model,
    allow_dangerous_deserialization=True
)

# Retriever
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# LLM (via Ollama)
llm = OllamaLLM(model="tinyllama")

# Prompt
prompt_template = PromptTemplate(
    input_variables=["context", "question"],
    template="""
You are a helpful assistant. Use the following context to answer the user's question.

Context:
{context}

Question: {question}

Answer:"""
)

# Retrieval QA
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    chain_type="stuff",
    chain_type_kwargs={"prompt": prompt_template}
)

# Interactive loop
while True:
    query = input("\nAsk a question (or type 'exit'): ")
    if query.lower() == "exit":
        break
    result = qa_chain.invoke(query)  # <-- updated method
    print(f"\n🧠 Answer:\n{result}")
