import os
import asyncio
import psycopg2
import uuid
from typing import Annotated
from pydantic import BaseModel

from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, OpenAIChatPromptExecutionSettings
from semantic_kernel.functions import kernel_function, KernelArguments

from semantic_kernel import Kernel
from semantic_kernel.connectors.memory.postgres import PostgresMemoryStore
from semantic_kernel.memory.semantic_text_memory import SemanticTextMemory
from semantic_kernel.connectors.ai.open_ai.services.azure_text_embedding import AzureTextEmbedding

AZURE_OPENAI_ENDPOINT   = ""
AZURE_OPENAI_KEY        = ""
AZURE_OPENAI_DEPLOYMENT = "gpt-4o"

DB_CONFIG = {
    "host":     "",
    "dbname":   "cases",
    "user":     "",
    "password": "",
    "port":     5432,
    "sslmode":  "require"
}


class PgPlugin:
        def __init__(self, cfg):
            self.cfg = cfg

        @kernel_function(description="Return the total number of cases in the database.")
        def count_cases(self) -> str:
            
            print("count_cases was called")
            
            conn = psycopg2.connect(**self.cfg)
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM cases;")
            n = cur.fetchone()[0]
            conn.close()
            return str(n)

        @kernel_function(description="Find up to 10 case IDs and names whose opinion contains the given keyword.")
        def search_cases(self, keyword: str) -> str:
            
            print("search_cases was called")
            
            conn = psycopg2.connect(**self.cfg)
            cur = conn.cursor()
            cur.execute(
                "SELECT id, name, opinion FROM cases WHERE opinion ILIKE %s LIMIT 10;",
                (f"%{keyword}%",)
            )
            rows = cur.fetchall()
            conn.close()
            if not rows:
                return "No matches"
            return "\n".join(f"{r[0]}: {r[1]}" for r in rows)

        @kernel_function(description="Use an advanced accuracy query to find important cases with high levels of citations about the query topic.")
        def search_graph_cases(self, query: str) -> str:
            
            print("search_graph_cases was called")
            
            conn = psycopg2.connect(**self.cfg)
            cur = conn.cursor()
            cur.execute(
                """
                SET search_path = public, ag_catalog, "$user";

                WITH semantic_ranked AS (
                    SELECT id, name, opinion, opinions_vector
                    FROM cases
                    ORDER BY opinions_vector <=> azure_openai.create_embeddings('text-embedding-3-small', %s)::vector
                    LIMIT 60
                ),
                graph AS (
                    SELECT graph_query.refs, semantic_ranked.*, graph_query.case_id 
                    FROM semantic_ranked
                    LEFT JOIN cypher('case_graph', $$
                        MATCH ()-[r]->(n)
                        RETURN n.case_id, COUNT(r) AS refs
                    $$) as graph_query(case_id TEXT, refs BIGINT)
                    ON semantic_ranked.id = graph_query.case_id::int
                )
                SELECT id, name, opinion
                FROM graph
                ORDER BY refs DESC NULLS LAST
                LIMIT 10;
                """, 
                (f"%{query}%",)
            )
            rows = cur.fetchall()
            conn.close()
            if not rows:
                return "No matches"
            return "\n".join(f"{r[0]}: {r[1]}: {r[2][:1000]}" for r in rows)



        @kernel_function(description="Use semantic re-ranking function to query and find cases matching the query based on semantic intent and relevance.  Use this function when high accuracy is needed.")
        def search_semantic_reranked_cases(self, query: str) -> str:
            
            print("search_semantic_reranked_cases was called")
            
            conn = psycopg2.connect(**self.cfg)
            cur = conn.cursor()
            cur.execute(
                """
                WITH embedding_query AS (
                    SELECT azure_openai.create_embeddings('text-embedding-3-small', %s)::vector AS embedding
                ),
                vector AS (
                    SELECT cases.id as case_id, cases.name AS case_name, cases.opinion, RANK() OVER (ORDER BY opinions_vector <=> embedding) AS vector_rank
                    FROM cases, embedding_query
                    ORDER BY opinions_vector <=> embedding
                    LIMIT 60
                ),
                semantic AS (
                    SELECT * 
                    FROM jsonb_array_elements(
                            semantic_relevance(%s, 60)
                        ) WITH ORDINALITY AS elem(relevance)
                ),
                semantic_ranked AS (
                    SELECT semantic.relevance::DOUBLE PRECISION AS relevance, RANK() OVER (ORDER BY relevance DESC) AS semantic_rank,
                            semantic.*, vector.*
                    FROM vector
                    JOIN semantic ON vector.vector_rank = semantic.ordinality
                    ORDER BY semantic.relevance DESC
                )
                SELECT case_id, case_name, opinion
                FROM semantic_ranked
                LIMIT 10;
                """, (query, query))
            rows = cur.fetchall()
            conn.close()
            if not rows:
                return "No matches"
            return "\n".join(f"{r[0]}: {r[1]}: {r[2][:1000]}" for r in rows)

















async def main():
    # Configure structured output format
    settings = OpenAIChatPromptExecutionSettings()
    

    chat_svc = AzureChatCompletion(
        deployment_name=AZURE_OPENAI_DEPLOYMENT,
        endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_KEY)

    # Create agent with plugin and settings
    agent = ChatCompletionAgent(
        service=chat_svc,
        name="SK-Assistant",
        instructions="You are a helpful legal assistant.  Respond to the user with the name of the cases and reasoning why the cases are the most relevant, and a short sentence summary of the opinion of the cases.",
        plugins=[PgPlugin(DB_CONFIG)],
        arguments=KernelArguments(settings)
    )

    conn_str = (
    f"host={DB_CONFIG['host']} "
    f"port={DB_CONFIG['port']} "
    f"dbname={DB_CONFIG['dbname']} "
    f"user={DB_CONFIG['user']} "
    f"password={DB_CONFIG['password']} "
    f"sslmode={DB_CONFIG['sslmode']}"
    )

    memory_store = PostgresMemoryStore(
        connection_string=conn_str,
        default_dimensionality=1536
    )

    embedding_generator = AzureTextEmbedding(
        deployment_name="text-embedding-3-small",
        endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_KEY
    )

    semantic_memory = SemanticTextMemory(
        storage=memory_store,
        embeddings_generator=embedding_generator
    )

    #user_query = "Find me 10 cases regarding the notion of water leaking."
    user_query = "How many cases are there, and high accuracy is important, help me find 10 highly relevant cases related to water leaking in my apartment."
    #user_query = "Help me find 10 highly relevant cases related to water leaking in my personal home apartment from the floor above.  High accuracy is important, and high number of citations is important.  Also how many cases are there overall?"
    #user_query = "Bring into 1 list of 10 cases, ranked by relevancy -- Help me find 10 highly relevant cases related to water leaking in my personal home apartment from the floor above.  High accuracy is important, and high number of citations is important."
    



    # ─── Save the user query into memory ─────────────────────────────────────────
    await semantic_memory.save_information(
        collection="agent_memories",
        text=user_query,
        id=str(uuid.uuid4()),
        description="User query"
    )

    # ─── Retrieve top-3 related memories for context ────────────────────────────
    recalls = await semantic_memory.search(
        collection="agent_memories",
        query=user_query,
        limit=3
    )
    # Build a little bullet list
    memory_context = "\n".join(f"- {m.text}" for m in recalls)

    # ─── Prepend memory to the prompt ────────────────────────────────────────────
    prompt = (
        f"Here are things we’ve discussed before:\n{memory_context}\n\n"
        f"{user_query}"
    )
    response = await agent.get_response(messages=prompt)
    
    print("prompt with memory context")
    print(prompt)

    print("response.content")
    print(response.content)
    
    

    # ─── Save the agent’s reply back to memory ─────────────────────────────────
    await semantic_memory.save_information(
        collection="agent_memories",
        text=str(response.content),
        id=str(uuid.uuid4()),
        description="Agent reply"
    )



    #response = await agent.get_response(messages="How many cases are there, and high accuracy is important, help me find 10 highly relevant cases related to water leaking in my apartment.")
    #response = await agent.get_response(messages="Help me find 10 highly relevant cases related to water leaking in my personal home apartment from the floor above.  High accuracy is important, and high number of citations is important.  Also how many cases are there overall?")
    #response = await agent.get_response(messages="Bring into 1 list of 10 cases, ranked by relevancy -- Help me find 10 highly relevant cases related to water leaking in my personal home apartment from the floor above.  High accuracy is important, and high number of citations is important.")
    #response = await agent.get_response(messages="Find me 10 cases regarding the notion of water leaking.")
    #print(response.content)

asyncio.run(main()) 