from fastapi import FastAPI, HTTPException
import google.generativeai as genai
import mysql.connector
import os
import re

app = FastAPI()
GEMINI_API_KEY = "AIzaSyAJQ9Cl1ZNsdlG2IG1hoyiYax3JQrwwF9w"
genai.configure(api_key=GEMINI_API_KEY)


MYSQL_CONFIG = {
    "host": "localhost",
    "user": "root",  
    "password": "Deepak@123",
    "database": "check"
}




def generate_sql(natural_query):
    """ Uses Gemini API to generate SQL from natural language """
    prompt =  f"""
     Convert the following natural language query into a MySQL query.
     Output **only** the SQL statement without Markdown formatting:

     {natural_query}
     """
    model = genai.GenerativeModel("gemini-1.5-pro-latest")

    try:
        response = model.generate_content(prompt)
        sql_query = response.text.strip()
        return sql_query
    except Exception as e:
        return e

def execute_sql(query):
    """Executes the SQL query on MySQL and returns results if applicable."""
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
 
        cursor.execute(query)
 
        
        if query.strip().lower().startswith("select"):
            result = cursor.fetchall() 
            column_names = [desc[0] for desc in cursor.description]  

           
            result = [dict(zip(column_names, row)) for row in result]   

        else:
            conn.commit()  
            result = { f"Query executed successfully. Rows affected: {cursor.rowcount}"}
            

        cursor.close()
        conn.close()

        return result
    except mysql.connector.Error as e:
        raise HTTPException(status_code=500, detail=f"MySQL Error: {str(e)}")

    

@app.get("/query")
def process_query(natural_query: str):
    sql_query = generate_sql(natural_query) 
    results = execute_sql(sql_query)

    if isinstance(results, dict):
        return {"sql_query": sql_query, **results}

    return { "sql_query": sql_query,"results": results}

