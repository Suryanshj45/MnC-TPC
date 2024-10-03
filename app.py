import streamlit as st
import sqlite3
import pandas as pd
import io

# Connect to SQLite database (it will create one if it doesn't exist)
conn = sqlite3.connect('college_company.db')
c = conn.cursor()

# Create tables if they don't exist
c.execute('''
CREATE TABLE IF NOT EXISTS companies (
    id INTEGER PRIMARY KEY,
    company_name TEXT,
    role TEXT,
    ctc REAL
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

def fetch_all_data_sorted(sort_by="college_name"):
    query = f'''
    SELECT colleges.college_name, companies.company_name, companies.role, companies.ctc 
    FROM colleges 
    JOIN companies ON colleges.company_id = companies.id
    ORDER BY {sort_by}
    '''
    c.execute(query)
    return c.fetchall()

def search_by_college(college_name):
    c.execute('''
    SELECT companies.company_name, companies.role, companies.ctc 
    FROM companies 
    JOIN colleges ON companies.id = colleges.company_id 
    WHERE LOWER(colleges.college_name) = LOWER(?)
    ''', (college_name,))
    return c.fetchall()

def search_by_company(company_name):
    c.execute('''
    SELECT colleges.college_name, companies.role, companies.ctc 
    FROM colleges 
    JOIN companies ON colleges.company_id = companies.id 
    WHERE LOWER(companies.company_name) = LOWER(?)
    ''', (company_name,))
    return c.fetchall()

def search_by_role(role):
    c.execute('''
    SELECT colleges.college_name, companies.company_name, companies.ctc 
    FROM colleges 
    JOIN companies ON colleges.company_id = companies.id 
    WHERE LOWER(companies.role) = LOWER(?)
    ''', (role,))
    return c.fetchall()

def search_with_filters(college_name=None, company_name=None, role=None):
    query = '''
    SELECT colleges.college_name, companies.company_name, companies.role, companies.ctc 
    FROM colleges 
    JOIN companies ON colleges.company_id = companies.id
    WHERE 1=1
    '''
    params = []
    
    if college_name:
        query += " AND LOWER(colleges.college_name) = LOWER(?)"
        params.append(college_name)
    
    if company_name:
        query += " AND LOWER(companies.company_name) = LOWER(?)"
        params.append(company_name)
    
    if role:
        query += " AND LOWER(companies.role) = LOWER(?)"
        params.append(role)
    
    c.execute(query, tuple(params))
    return c.fetchall()

def update_data(college_name, new_company_name, new_role, new_ctc):
    c.execute('''
    UPDATE companies
    SET company_name = ?, role = ?, ctc = ?
    WHERE id IN (SELECT company_id FROM colleges WHERE college_name = ?)
    ''', (new_company_name, new_role, new_ctc, college_name))
    conn.commit()

def delete_data(college_name):
    c.execute('''
    DELETE FROM companies
    WHERE id IN (SELECT company_id FROM colleges WHERE college_name = ?)
    ''', (college_name,))
    c.execute('''
    DELETE FROM colleges WHERE college_name = ?
    ''', (college_name,))
    conn.commit()

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

elif option == "Search":
    search_option = st.selectbox("Search by:", ("College Name", "Company Name", "Role", "Filter by Multiple Criteria"))
    
    if search_option == "College Name":
        college_name = st.text_input("Enter College Name to Search")
        if st.button("Search"):
            if college_name:
                results = search_by_college(college_name)
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
                results = search_by_company(company_name)
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
                results = search_by_role(role)
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
            results = search_with_filters(college_name, company_name, role)
            if results:
                df = pd.DataFrame(results, columns=["College Name", "Company Name", "Role", "CTC"])
                st.dataframe(df)
            else:
                st.write("No results found.")

elif option == "Edit/Delete":
    college_name = st.text_input("Enter College Name to Edit/Delete")
    
    if st.button("Search for Edit/Delete"):
        if college_name:
            results = search_by_college(college_name)
            if results:
                company_name = results[0][0]
                role = results[0][1]
                ctc = results[0][2]
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
                            update_data(college_name, new_company_name, new_role, new_ctc_float)
                            st.success("Data updated successfully!")
                        except ValueError:
                            st.error("Please enter a valid decimal number for CTC.")
                    else:
                        st.warning("Please fill in all fields.")

                # Button to delete data
                if st.button("Delete Data"):
                    delete_data(college_name)
                    st.success("Data deleted successfully!")
            else:
                st.write("No results found.")

elif option == "View All Data":
    sort_option = st.selectbox("Sort by:", ("College Name", "Company Name", "Role", "CTC"))
    results = fetch_all_data_sorted(sort_by=sort_option.lower().replace(" ", "_"))
    df = pd.DataFrame(results, columns=["College Name", "Company Name", "Role", "CTC"])
    
    st.dataframe(df)

conn.close()
