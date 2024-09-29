import streamlit as st
import sqlite3
import pandas as pd

# Connect to SQLite database (it will create one if it doesn't exist)
conn = sqlite3.connect('college_company.db')
c = conn.cursor()

# Create tables if they don't exist
c.execute('''
CREATE TABLE IF NOT EXISTS companies (
    id INTEGER PRIMARY KEY,
    company_name TEXT,
    role TEXT,
    ctc REAL  -- Change to REAL for decimal values
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS colleges (
    id INTEGER PRIMARY KEY,
    college_name TEXT,
    company_id INTEGER,
    FOREIGN KEY (company_id) REFERENCES companies (id)
)
''')

# Function to add data
def add_data(college_name, company_name, role, ctc):
    c.execute('INSERT INTO companies (company_name, role, ctc) VALUES (?, ?, ?)', (company_name, role, ctc))
    company_id = c.lastrowid
    c.execute('INSERT INTO colleges (college_name, company_id) VALUES (?, ?)', (college_name, company_id))
    conn.commit()

# Function to fetch all data
def fetch_all_data():
    c.execute('''
    SELECT colleges.college_name, companies.company_name, companies.role, companies.ctc 
    FROM colleges 
    JOIN companies ON colleges.company_id = companies.id
    ''')
    return c.fetchall()

# Function to search by college name (case-insensitive)
def search_by_college(college_name):
    c.execute('''
    SELECT companies.company_name, companies.role, companies.ctc 
    FROM companies 
    JOIN colleges ON companies.id = colleges.company_id 
    WHERE LOWER(colleges.college_name) = LOWER(?)
    ''', (college_name,))
    return c.fetchall()

# Function to search by company name (case-insensitive)
def search_by_company(company_name):
    c.execute('''
    SELECT colleges.college_name, companies.role, companies.ctc 
    FROM colleges 
    JOIN companies ON colleges.company_id = companies.id 
    WHERE LOWER(companies.company_name) = LOWER(?)
    ''', (company_name,))
    return c.fetchall()

# Function to search by role (case-insensitive)
def search_by_role(role):
    c.execute('''
    SELECT colleges.college_name, companies.company_name, companies.ctc 
    FROM colleges 
    JOIN companies ON colleges.company_id = companies.id 
    WHERE LOWER(companies.role) = LOWER(?)
    ''', (role,))
    return c.fetchall()

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

option = st.selectbox("Do you want to Search, Add Data, or View All Data?", ("Search", "Add", "View All Data"))

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
                add_data(st.session_state.college_name, st.session_state.company_name, st.session_state.role, ctc_float)
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

    # Button to add another entry
    if st.button("Add Another Entry"):
        st.session_state.college_name = ""
        st.session_state.company_name = ""
        st.session_state.role = ""
        st.session_state.ctc = ""

    st.write("You can continue adding more entries.")

elif option == "Search":
    search_option = st.selectbox("Search by:", ("College Name", "Company Name", "Role"))
    
    if search_option == "College Name":
        college_name = st.text_input("Enter College Name to Search")
        if st.button("Search"):
            if college_name:
                results = search_by_college(college_name)
                if results:
                    st.write("Results:")
                    for row in results:
                        st.write(f"Company: {row[0]}, Role: {row[1]}, CTC: {row[2]:.2f}")
                else:
                    st.write("No results found.")
            else:
                st.warning("Please enter a college name.")

    elif search_option == "Company Name":
        company_name = st.text_input("Enter Company Name to Search")
        if st.button("Search"):
            if company_name:
                results = search_by_company(company_name)
                if results:
                    st.write("Results:")
                    for row in results:
                        st.write(f"College: {row[0]}, Role: {row[1]}, CTC: {row[2]:.2f}")
                else:
                    st.write("No results found.")
            else:
                st.warning("Please enter a company name.")

    elif search_option == "Role":
        role = st.text_input("Enter Role to Search")
        if st.button("Search"):
            if role:
                results = search_by_role(role)
                if results:
                    st.write("Results:")
                    for row in results:
                        st.write(f"College: {row[0]}, Company: {row[1]}, CTC: {row[2]:.2f}")
                else:
                    st.write("No results found.")
            else:
                st.warning("Please enter a role.")

elif option == "View All Data":
    if st.button("Show All Data"):
        all_data = fetch_all_data()
        if all_data:
            # Create a DataFrame to display the data
            df = pd.DataFrame(all_data, columns=["College Name", "Company Name", "Role", "CTC"])
            st.write(df)
        else:
            st.write("No data available.")

conn.close()
