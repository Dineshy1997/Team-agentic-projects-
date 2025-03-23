import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000/query"  # Ensure your FastAPI server is running

st.title("MySQL Query Generator")

# User Input
natural_query = st.text_input("Enter your natural language query:")

if st.button("Generate SQL"):
    if natural_query:
        response = requests.get(API_URL, params={"natural_query": natural_query})
        
        if response.status_code == 200:
            data = response.json()
            if "sql_query" in data:
                st.subheader("Generated SQL Query:")
                st.code(data["sql_query"], language="sql")  # Display SQL query

                st.subheader("Query Results:")
                if "results" in data:
                    st.write(data["results"])  # Display MySQL results
                else:
                    st.warning("No results found.")
            else:
                st.error("Failed to generate SQL query.")
        else:
            st.error(f"API Error: {response.status_code}, {response.text}")
    else:
        st.warning("Please enter a query.")

