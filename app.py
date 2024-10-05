import streamlit as st
import psycopg2
import pandas as pd
import io, os
import sqlite3
from urllib.parse import urlparse
from typing import NewType, Union
from abc import ABC, abstractmethod

# DEBUG Load environment variables from .env file
from dotenv import load_dotenv; load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# TODO: when we have multiple companies to same collage the in search of edit/delete first list all then edit/delete them.
# TODO: delete functionality is not working yet.

class DATABASE(ABC):
    @abstractmethod
    def commit(self): ...
    @abstractmethod
    def close(self): ...
    @abstractmethod
    def create_tables(self): ...
    @abstractmethod
    def add_data(self, college_name, company_name, role, ctc): ...
    @abstractmethod
    def fetch_all_data(self): ...
    @abstractmethod
    def fetch_all_data_sorted(self, sort_by="college_name"): ...
    @abstractmethod
    def search_by_college(self, college_name): ...
    @abstractmethod
    def search_by_company(self, company_name): ...
    @abstractmethod
    def search_by_role(self, role): ...
    @abstractmethod
    def search_with_filters(self, college_name=None, company_name=None, role=None): ... 
    @abstractmethod
    def update_data(self, college_name, new_company_name, new_role, new_ctc): ...
    @abstractmethod
    def delete_data(self, college_name): ...
        
class PostgreSQL(DATABASE):
    def __init__(self, db_url):
        parsed_url = urlparse(db_url)
        
        # Connect to PostgreSQL database
        self.conn:psycopg2.connection = psycopg2.connect(
            dbname=parsed_url.path[1:],  # Remove the leading '/' 
            user=parsed_url.username,
            password=parsed_url.password, 
            host=parsed_url.hostname, 
            port=parsed_url.port
        )
        
        self.create_tables()
    
    def commit(self): return self.conn.commit()
    def close(self): return self.conn.close()
    
    # Create tables if they don't exist
    def create_tables(self):
        with self.conn.cursor() as c:
            c.execute('''
            CREATE TABLE IF NOT EXISTS companies (
                id SERIAL PRIMARY KEY,
                company_name TEXT,
                role TEXT,
                ctc REAL
            )
            ''')

            c.execute('''
            CREATE TABLE IF NOT EXISTS colleges (
                id SERIAL PRIMARY KEY,
                college_name TEXT,
                company_id INTEGER,
                FOREIGN KEY (company_id) REFERENCES companies (id)
            )
            ''')
        self.commit()

    # Function to add data
    def add_data(self, college_name, company_name, role, ctc):
        with self.conn.cursor() as c:
            c.execute('INSERT INTO companies (company_name, role, ctc) VALUES (%s, %s, %s) RETURNING id', (company_name, role, ctc))
            company_id = c.fetchone()[0]
            c.execute('INSERT INTO colleges (college_name, company_id) VALUES (%s, %s)', (college_name, company_id))
        self.commit()

    # Function to fetch all data
    def fetch_all_data(self):
        with self.conn.cursor() as c:
            c.execute('''
            SELECT colleges.college_name, companies.company_name, companies.role, companies.ctc 
            FROM colleges 
            JOIN companies ON colleges.company_id = companies.id
            ''')
            return c.fetchall()
    def fetch_all_data_sorted(self, sort_by="college_name"):
        with self.conn.cursor() as c:
            query = f'''
            SELECT colleges.college_name, companies.company_name, companies.role, companies.ctc 
            FROM colleges 
            JOIN companies ON colleges.company_id = companies.id
            ORDER BY {sort_by}
            '''
            c.execute(query)
            return c.fetchall()
    def search_by_college(self, college_name):
        with self.conn.cursor() as c:
            c.execute('''
            SELECT companies.company_name, companies.role, companies.ctc 
            FROM companies 
            JOIN colleges ON companies.id = colleges.company_id 
            WHERE LOWER(colleges.college_name) = LOWER(%s)
            ''', (college_name,))
            return c.fetchall()

    def search_by_company(self, company_name):
        with self.conn.cursor() as c:
            c.execute('''
            SELECT colleges.college_name, companies.role, companies.ctc 
            FROM colleges 
            JOIN companies ON colleges.company_id = companies.id 
            WHERE LOWER(companies.company_name) = LOWER(%s)
            ''', (company_name,))
            return c.fetchall()
    def search_by_role(self, role):
        with self.conn.cursor() as c:
            c.execute('''
            SELECT colleges.college_name, companies.company_name, companies.ctc 
            FROM colleges 
            JOIN companies ON colleges.company_id = companies.id 
            WHERE LOWER(companies.role) = LOWER(%s)
            ''', (role,))
            return c.fetchall()

    def search_with_filters(self, college_name=None, company_name=None, role=None):
        query = '''
        SELECT colleges.college_name, companies.company_name, companies.role, companies.ctc 
        FROM colleges 
        JOIN companies ON colleges.company_id = companies.id
        WHERE 1=1
        '''
        params = []

        if college_name:
            query += " AND LOWER(colleges.college_name) = LOWER(%s)"
            params.append(college_name)

        if company_name:
            query += " AND LOWER(companies.company_name) = LOWER(%s)"
            params.append(company_name)

        if role:
            query += " AND LOWER(companies.role) = LOWER(%s)"
            params.append(role)

        with self.conn.cursor() as c:
            c.execute(query, params)
            return c.fetchall()

    def update_data(self, college_name, new_company_name, new_role, new_ctc):
        with self.conn.cursor() as c:
            c.execute('''
            UPDATE companies
            SET company_name = %s, role = %s, ctc = %s
            WHERE id IN (SELECT company_id FROM colleges WHERE college_name = %s)
            ''', (new_company_name, new_role, new_ctc, college_name))
        self.commit()

    def delete_data(self, college_name):
        with self.conn.cursor() as c:
            c.execute('''
            DELETE FROM companies
            WHERE id IN (SELECT company_id FROM colleges WHERE college_name = %s)
            ''', (college_name,))
            c.execute('''
            DELETE FROM colleges WHERE college_name = %s
            ''', (college_name,))
        self.commit()

# NOTE: In a typical Streamlit application, the entire script is rerun on every interaction, such as when a user inputs data or clicks a button.
# Function to connect to the database
def get_db_connection():
    if 'db' not in st.session_state:
        st.session_state.db = PostgreSQL(db_url=DATABASE_URL) 
        st.write("Connected to database.")
    return st.session_state.db

# Initialize the database connection
db = get_db_connection() # Fn Once

# Initialize session state for form fields if not already present
if 'college_name' not in st.session_state:
    st.session_state.college_name = ""
if 'company_name' not in st.session_state:
    st.session_state.company_name = ""
if 'role' not in st.session_state:
    st.session_state.role = ""
if 'ctc' not in st.session_state:
    st.session_state.ctc = ""

# Streamlit UI
st.title("College and Company Dashboard")

option = st.selectbox("Do you want to Search, Add Data, Edit/Delete, or View All Data?", ("Search", "Add", "Edit/Delete", "View All Data"))

if option == "Add":
    # Create text input fields for data entry
    st.session_state.college_name = st.text_input("Enter College Name", value=st.session_state.college_name)
    st.session_state.company_name = st.text_input("Enter Company Name", value=st.session_state.company_name)
    st.session_state.role = st.text_input("Enter Role", value=st.session_state.role)
    st.session_state.ctc = st.text_input("Enter CTC (Decimal Only)", placeholder="e.g., 50000.00", value=st.session_state.ctc)

    # Button to add data
    if st.button("Add Data"):
        if st.session_state.college_name and st.session_state.company_name and st.session_state.role and st.session_state.ctc:
            try:
                ctc_float = float(st.session_state.ctc)  # Convert CTC to float
                db.add_data(st.session_state.college_name, st.session_state.company_name, st.session_state.role, ctc_float)
                st.success("Data added successfully!")
                
                # Clear the input fields for new entry
                st.session_state.college_name = ""
                st.session_state.company_name = ""
                st.session_state.role = ""
                st.session_state.ctc = ""
            except ValueError:
                st.error("Please enter a valid decimal number for CTC.")
        else:
            st.warning("Please fill in all fields.")

elif option == "Search":
    search_option = st.selectbox("Search by:", ("College Name", "Company Name", "Role", "Filter by Multiple Criteria"))
    
    if search_option == "College Name":
        college_name = st.text_input("Enter College Name to Search")
        if st.button("Search"):
            if college_name:
                results = db.search_by_college(college_name)
                if results:
                    df = pd.DataFrame(results, columns=["Company Name", "Role", "CTC"])
                    st.dataframe(df)  # Display the results in a table format
                else:
                    st.write("No results found.")
            else:
                st.warning("Please enter a college name.")

    elif search_option == "Company Name":
        company_name = st.text_input("Enter Company Name to Search")
        if st.button("Search"):
            if company_name:
                results = db.search_by_company(company_name)
                if results:
                    df = pd.DataFrame(results, columns=["College Name", "Role", "CTC"])
                    st.dataframe(df)  # Display the results in a table format
                else:
                    st.write("No results found.")
            else:
                st.warning("Please enter a company name.")

    elif search_option == "Role":
        role = st.text_input("Enter Role to Search")
        if st.button("Search"):
            if role:
                results = db.search_by_role(role)
                if results:
                    df = pd.DataFrame(results, columns=["College Name", "Company Name", "CTC"])
                    st.dataframe(df)  # Display the results in a table format
                else:
                    st.write("No results found.")
            else:
                st.warning("Please enter a role.")
    
    elif search_option == "Filter by Multiple Criteria":
        college_name = st.text_input("Enter College Name (optional)")
        company_name = st.text_input("Enter Company Name (optional)")
        role = st.text_input("Enter Role (optional)")
        
        if st.button("Search with Filters"):
            results = db.search_with_filters(college_name, company_name, role)
            if results:
                df = pd.DataFrame(results, columns=["College Name", "Company Name", "Role", "CTC"])
                st.dataframe(df)
            else:
                st.write("No results found.")

elif option == "Edit/Delete":
    college_name = st.text_input("Enter College Name to Edit/Delete", value=st.session_state.get('college_name', ''))
    
    if st.button("Search for Edit/Delete"):
        if college_name:
            results = db.search_by_college(college_name)
            if results:
                # Store the results in session state
                st.session_state['company_name'] = results[0][0]
                st.session_state['role'] = results[0][1]
                st.session_state['ctc'] = results[0][2]
                st.success("Search completed! You can now edit or delete.")
            else:
                st.write("No results found.")
                st.session_state['company_name'] = ""
                
    if st.session_state["company_name"]:  # Check if we have searched for a college
        # Display current values
        company_name = st.session_state['company_name']
        role = st.session_state['role']
        ctc = st.session_state['ctc']
        st.write(f"Company: {company_name}, Role: {role}, CTC: {ctc}")
        
        # Input fields for new data
        new_company_name = st.text_input("New Company Name", value=company_name)
        new_role = st.text_input("New Role", value=role)
        new_ctc = st.text_input("New CTC (Decimal Only)", value=str(ctc))

        # Button to update data
        if st.button("Update Data"):
            if new_company_name and new_role and new_ctc:
                try:
                    new_ctc_float = float(new_ctc)
                    db.update_data(college_name, new_company_name, new_role, new_ctc_float)
                    st.success("Data updated successfully!")
                    # clear the session state after successful update
                    st.session_state['company_name'] = ""
                    st.session_state['role'] = ""
                    st.session_state['ctc'] = ""
                except ValueError:
                    st.error("Please enter a valid decimal number for CTC.")
            else:
                st.warning("Please fill in all fields.")

        # Button to delete data
        if st.button("Delete Data"):
            db.delete_data(college_name)
            st.success("Data deleted successfully!")
            # Clear session state after deletion if desired
            st.session_state['company_name'] = ""
            st.session_state['role'] = ""
            st.session_state['ctc'] = ""
    else:
        st.session_state['company_name'] = ""
        st.session_state['role'] = ""
        st.session_state['ctc'] = ""

elif option == "View All Data":
    sort_option = st.selectbox("Sort by:", ("College Name", "Company Name", "Role", "CTC"))
    results = db.fetch_all_data_sorted(sort_by=sort_option.lower().replace(" ", "_"))
    df = pd.DataFrame(results, columns=["College Name", "Company Name", "Role", "CTC"])
    
    st.dataframe(df)

# db.close()
# NOTE: In a typical Streamlit application, the entire script is rerun on every interaction, such as when a user inputs data or clicks a button.
