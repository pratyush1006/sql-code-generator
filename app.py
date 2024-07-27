from dotenv import load_dotenv
load_dotenv()  # Load all the environment variables

import streamlit as st
import os
import pandas as pd
import mysql.connector  # Import mysql.connector for MySQL operations
import google.generativeai as genai

# Configure the API key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-pro')

def read_sql_query(sql, host, user, password, database):
    try:
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        columns = [i[0] for i in cur.description]  # Get column names
        
        conn.close()
        
        df = pd.DataFrame(rows, columns=columns)
        df = df.loc[:, ~df.columns.duplicated()]  # Remove duplicate columns
        
        return df
    except mysql.connector.Error as err:
        if err.errno == 1045:
            st.error("Access denied: Check your username and password and try again.")
        elif err.errno == 2003:
            st.error("Cannot connect to MySQL server: Ensure the server is running and accessible.")
        elif err.errno == 1049:
            st.error("Unknown database: Verify the database name.")
        elif err.errno == 1146:
            st.error("Table doesn't exist: Verify the table name.")
        else:
            st.error(f"Error: {err}")
        return None

def main():
    st.set_page_config(page_title="I can Retrieve Any SQL query", page_icon=":robot:")
    st.markdown(
        """<div style="text-align: center;">
            <h1>Sql Query Generator</h1>
            <h3>I can generate SQL Query for you!</h3>
            <h4>With explanation as well!!!</h4>
            <p>This tool is a simple tool that can generate SQL Queries based on your prompt.</p> 
        </div>
        """,
        unsafe_allow_html=True,
    )

    host = st.text_input("MySQL Host", key="host", value="localhost")
    user = st.text_input("MySQL User", key="user")
    password = st.text_input("MySQL Password", type="password", key="password")
    database = st.text_input("MySQL Database", key="database")
    text_input = st.text_area("Enter your query")

    submit = st.button("Generate SQL Query")

    if submit:
        with st.spinner("Generating SQL Query..."):
            template = """
                create a SQL Query snippet using the below text:
                {text_input}
                I just want a SQL Query.
            """
            formatted_template = template.format(text_input=text_input)

            response = model.generate_content(formatted_template)
            sql_query = response.text.strip().lstrip("```sql").rstrip("```")
            
            query_results = read_sql_query(sql_query, host, user, password, database)
            if query_results is not None:
                # Generate expected output based on actual query results
                try:
                    expected_output = query_results.head().to_markdown()
                except ImportError:
                    expected_output = query_results.head().to_string()

                # Generate explanation using the actual query
                explanation_template = """
                    Explain this SQL Query:
                    '''
                    {sql_query}
                    '''
                    Please provide the simplest explanation:
                """
                explanation_formatted = explanation_template.format(sql_query=sql_query)
                explanation_response = model.generate_content(explanation_formatted)
                explanation = explanation_response.text
            
                with st.container():
                    st.success("SQL Query Generated Successfully! Here is your Query Below:")
                    st.code(sql_query, language="sql")

                    st.success("Query Results:")
                    st.dataframe(query_results)

                    st.success("Explanation of the given SQL Query:")
                    st.markdown(explanation)
            else:
                st.error("Failed to execute the generated SQL query. Please check the query and try again.")
                
main()
