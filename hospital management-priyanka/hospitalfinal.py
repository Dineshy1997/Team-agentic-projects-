import streamlit as st
import pyodbc
import datetime
import smtplib
import os
import pandas as pd
from fpdf import FPDF  # PDF Library
import google.generativeai as genai
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


# Set up Google Gemini API
GEMINI_API_KEY = "AIzaSyCXb7-P-SyuOMBGeW5x5xFK0V1aI0uIVrM" # Replace with your actual API key
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-pro")

# Database Connection
SERVER = "DESKTOP-F4API67\\SQLEXPRESS"  # Change this to your SQL Server name
DATABASE = "HospitalDB"

# Email Configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_SENDER = "priyangamuniyappan512002@gmail.com"  # Replace with your email
EMAIL_PASSWORD = "shso vkli erix xyny" # Use App Password for security


appointments = {}  # Dictionary to store patient appointments
def get_db_connection():
    try:
        conn = pyodbc.connect(f'DRIVER={{SQL Server}};SERVER={SERVER};DATABASE={DATABASE};Trusted_Connection=yes;')
        return conn
    except Exception as e:
        st.error(f"Database Connection Error: {e}")
        return None

# ✅ Function to Get the Next Available Patient ID
def get_next_patient_id():
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT ISNULL(MAX(HospitalID), 0) + 1 FROM Patients")  # Auto-increment next ID
        next_id = cursor.fetchone()[0]
        conn.close()
        return next_id
    return 1  # If no records exist, start from 1

# ✅ Function to Add Patient
def add_patient(name, phone, address, height, weight, blood_pressure, diseases, first_visit, billing_details, oxygen_level):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        hospital_id = get_next_patient_id()
        first_visit_str = first_visit.strftime('%Y-%m-%d')

        query = """INSERT INTO Patients (HospitalID, Name, Phone, Address, Height, Weight, BloodPressure, Diseases, FirstVisitDate, BillingDetails) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        cursor.execute(query, (hospital_id, name, phone, address, height, weight, blood_pressure, diseases, first_visit_str, billing_details))
        conn.commit()
        conn.close()
        st.success(f"✅ Patient Added Successfully! (Patient ID: {hospital_id})")

# ✅ Function to Add Visit for Returning Patients
def add_patient_visit(hospital_id, visit_date, symptoms, temperature, oxygen_level, blood_pressure):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        visit_date_str = visit_date.strftime('%Y-%m-%d')

        query = """INSERT INTO PatientVisits (HospitalID, VisitDate, Symptoms, Temperature, OxygenLevel, BloodPressure, OxygenLevel) 
                   VALUES (?, ?, ?, ?, ?, ?)"""
        cursor.execute(query, (hospital_id, visit_date_str, symptoms, temperature, oxygen_level, blood_pressure, oxygen_level))
        conn.commit()
        conn.close()
        st.success("✅ Visit Record Added Successfully!")

# ✅ Function to Retrieve Patient Records
def get_patient_record(hospital_id):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        query = "SELECT * FROM Patients WHERE HospitalID = ?"
        cursor.execute(query, (hospital_id,))
        record = cursor.fetchone()
        conn.close()
        return record
    return None

# ✅ Function to Retrieve Visit History
#def get_visit_history(hospital_id):
 #   conn = get_db_connection()
  #  if conn:
  #      cursor = conn.cursor()
  #      query = "SELECT VisitDate, Symptoms, Temperature, OxygenLevel, BloodPressure FROM PatientVisits WHERE HospitalID = ? ORDER BY VisitDate DESC"
  #      cursor.execute(query, (hospital_id,))
   #     visits = cursor.fetchall()
   #     conn.close()
   #     return visits
  #  return None


def add_patient_visit(hospital_id, visit_date, symptoms, temperature, oxygen_level, blood_pressure):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        visit_date_str = visit_date.strftime('%Y-%m-%d')

        query = """INSERT INTO PatientVisits (HospitalID, VisitDate, Symptoms, Temperature, OxygenLevel, BloodPressure) 
                   VALUES (?, ?, ?, ?, ?, ?)"""  # ✅ Fixed query

        cursor.execute(query, (hospital_id, visit_date_str, symptoms, temperature, oxygen_level, blood_pressure))  # ✅ 6 values
        conn.commit()
        conn.close()
        st.success("✅ Visit Record Added Successfully!")

# -------------------- EMAIL FUNCTION --------------------

def send_email(receiver_email, patient_id, appointment_date, subject, body):
    """Send an email notification (confirmation or reminder)."""
    msg = MIMEMultipart()
    msg["From"] = EMAIL_SENDER
    msg["To"] = receiver_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, receiver_email, msg.as_string())
        server.quit()
        return "📩 Email Sent Successfully!"
    except Exception as e:
        return f"❌ Failed to send email: {str(e)}"


# -------------------- APPOINTMENT BOOKING --------------------

def book_appointment(patient_id, date, email):
    """Book an appointment and send confirmation email."""
    if patient_id in appointments:
        return f"⚠️ Patient {patient_id} already has an appointment on {appointments[patient_id]['date']}."

    appointments[patient_id] = {"date": date, "email": email}

    # Print stored data for debugging
    print("Appointments Dictionary:", appointments)

    # Send Confirmation Email
    subject = "Appointment Confirmation - Hospital"
    body = f"""
    Dear Patient {patient_id},

    Your appointment has been successfully booked for {date}.

    Thank you for choosing our hospital.

    Best Regards,
    Hospital Management
    """
    email_status = send_email(email, patient_id, date, subject, body)

    return f"✅ Appointment confirmed for Patient {patient_id} on {date}.\n{email_status}"


# -------------------- SEND REMINDER EMAILS --------------------

def send_reminders():
    """Send reminders to all patients who have an appointment tomorrow."""
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")

    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT patient_id, email, appointment_date FROM Appointments WHERE appointment_date = ?", (tomorrow,))
        reminders = cursor.fetchall()
        conn.close()

        if reminders:
            for patient_id, email, appointment_date in reminders:
                subject = "Appointment Reminder - Hospital"
                body = f"""
                Dear Patient {patient_id},

                This is a reminder that you have an appointment scheduled for {appointment_date}.
                Please ensure you arrive on time.

                Best Regards,
                Hospital Management
                """
                email_status = send_email(email, patient_id, appointment_date, subject, body)
                st.success(f"📩 Reminder sent to {email} ✅")
                print(f"Reminder sent to {email} - Status: {email_status}")
        else:
            st.info("✅ No reminders for tomorrow.")
            print("No reminders found for tomorrow.")


#  Auto-Generate Employee ID

def generate_employee_id():
    conn = get_db_connection()
    if conn is None:
        return None

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(EmployeeID) FROM Employees")
        max_id = cursor.fetchone()[0]

        conn.close()

        if max_id is None:
            return 1001  # Start from 1001 if no employees exist
        else:
            return max_id + 1

    except Exception as e:
        st.error(f"Error Generating Employee ID: {e}")
        return None



#  Function to Add Employee

def add_employee(full_name, department, role, contact, email, salary, join_date, shift, status):
    conn = get_db_connection()
    if conn is None:
        return

    try:
        cursor = conn.cursor()

        # Convert date to string format (YYYY-MM-DD)
        join_date_str = join_date.strftime("%Y-%m-%d")

        # Ensure salary is a float
        salary = float(salary)

        # Insert employee (Fix: Added 'Status' column to match values)
        cursor.execute("""
            INSERT INTO Employees (FullName, Department, Role, Contact, Email, Salary, JoinDate, Shift, Status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (full_name, department, role, contact, email, salary, join_date_str, shift, status))

        conn.commit()
        conn.close()
        st.success(f"✅ Employee '{full_name}' added successfully!")

    except Exception as e:
        st.error(f"❌ Error Adding Employee: {e}")



#  Function to Fetch Employee Details

def get_employee_details(employee_id):
    conn = get_db_connection()
    if conn is None:
        return None

    try:
        query = f"SELECT * FROM Employees WHERE EmployeeID = ?"
        df = pd.read_sql(query, conn, params=[employee_id])
        conn.close()

        if df.empty:
            return None
        return df.iloc[0]  # Return first matching record

    except Exception as e:
        st.error(f"❌ Error Fetching Employee Data: {e}")
        return None



#  Function to Generate PDF

def generate_employee_pdf(employee_data):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Arial", style='B', size=16)
    pdf.cell(200, 10, "Employee Details Report", ln=True, align='C')
    pdf.ln(10)

    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, f"Employee ID: {employee_data['EmployeeID']}", ln=True)
    pdf.cell(200, 10, f"Full Name: {employee_data['FullName']}", ln=True)
    pdf.cell(200, 10, f"Department: {employee_data['Department']}", ln=True)
    pdf.cell(200, 10, f"Role: {employee_data['Role']}", ln=True)
    pdf.cell(200, 10, f"Contact: {employee_data['Contact']}", ln=True)
    pdf.cell(200, 10, f"Email: {employee_data['Email']}", ln=True)
    pdf.cell(200, 10, f"Salary: ${employee_data['Salary']}", ln=True)
    pdf.cell(200, 10, f"Joining Date: {employee_data['JoinDate']}", ln=True)
    pdf.cell(200, 10, f"Shift: {employee_data['Shift']}", ln=True)
    pdf.cell(200, 10, f"Status: {employee_data['Status']}", ln=True)

    pdf_output_path = "employee_details.pdf"
    pdf.output(pdf_output_path)

    return pdf_output_path




#  Streamlit UI
st.title("🏥 Hospital & Employee Management System")

# Sidebar Main Menu
main_menu = st.sidebar.radio("📌 Select a Section", ["Patient Management", "Employee Management"])

choice=None
if main_menu == "Patient Management":
    menu = ["Register Patient", "Retrieve Patient Record", "Add Visit Record", "Book Appointment", "Reminders"]
    choice = st.sidebar.selectbox("📁 Patient Management Menu", menu)

# Sidebar Menu
#menu = ["Register Patient", "Retrieve Patient Record", "Add Visit Record","Book Appointment", "Reminders", "Register Employee", "View Employee Details & Download PDF"]
#choice = st.sidebar.selectbox("Select an Option", menu)

#  Register New Patient
if choice == "Register Patient":
    st.subheader("📝 Register New Patient")
    next_hospital_id = get_next_patient_id()
    st.write(f"**Next Available Patient ID:** {next_hospital_id}")

    name = st.text_input("Full Name")
    phone = st.text_input("Phone Number")
    address = st.text_area("Address")
    height = st.text_input("Height (cm)")
    weight = st.text_input("Weight (kg)")
    blood_pressure = st.text_input("Blood Pressure (e.g., 120/80)")
    oxygen_level=st.text_input("Oxygen Level")
    diseases = st.text_area("Existing Diseases")
    first_visit = st.date_input("First Visit Date", datetime.date.today())
    billing_details = st.text_area("Billing Details")

    if st.button("Add Patient"):
        add_patient(name, phone, address, height, weight, blood_pressure, diseases, first_visit, billing_details,oxygen_level)

#  Retrieve Patient Record
elif choice == "Retrieve Patient Record":
    st.subheader("🔍 Retrieve Patient Record")
    hospital_id = st.text_input("Enter Hospital ID to Search")

    if st.button("Get Patient Details"):
        record = get_patient_record(hospital_id)
        if record:
            st.write(f"**Name:** {record[1]}")
            st.write(f"**Phone:** {record[2]}")
            st.write(f"**Address:** {record[3]}")
            st.write(f"**Height:** {record[4]} cm")
            st.write(f"**Weight:** {record[5]} kg")
            st.write(f"**Blood Pressure:** {record[6]}")
            st.write(f"**Diseases:** {record[7]}")
            st.write(f"**First Visit Date:** {record[8]}")
            st.write(f"**Billing Details:** {record[9]}")
            st.write(f"**Oxygen Level:** {record[10]}")


            def get_visit_history(hospital_id):
                conn = get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    query = "SELECT VisitDate, Symptoms, Temperature, OxygenLevel, BloodPressure FROM PatientVisits WHERE HospitalID = ? ORDER BY VisitDate DESC"
                    cursor.execute(query, (hospital_id,))
                    visits = cursor.fetchall()
                    conn.close()
                    return visits
                return None


            # Display Visit History
            visits = get_visit_history(hospital_id)
            if visits:
                st.subheader("🗂 Visit History")
                for visit in visits:
                    st.write(f" **Date:** {visit[0]}")
                    st.write(f" **Symptoms:** {visit[1]}")
                    st.write(f"️ **Temperature:** {visit[2]} °C")
                    st.write(f" **Oxygen Level:** {visit[3]}%")
                    st.write(f" **Blood Pressure:** {visit[4]}")
                    st.markdown("---")
        #    else:
        #        st.warning("⚠️ No visit history found for this patient.")
        else:
            st.warning("⚠️ No record found for this Hospital ID.")

#  Add Visit Record for Returning Patients
elif choice == "Add Visit Record":
    st.subheader("📌 Add Visit Record")
    hospital_id = st.text_input("Enter Patient's Hospital ID")
    visit_date = st.date_input("Visit Date", datetime.date.today())
    symptoms = st.text_area("Symptoms")
    temperature = st.text_input("Temperature (°C)")
    oxygen_level = st.text_input("Oxygen Level (%)")
    blood_pressure = st.text_input("Blood Pressure (e.g., 120/80)")

    if st.button("Add Visit"):
        add_patient_visit(hospital_id, visit_date, symptoms, temperature, oxygen_level, blood_pressure)

elif choice == "Book Appointment":
    st.header("📅 Schedule an Appointment")
    patient_id = st.text_input("Enter Patient ID:")
    patient_email = st.text_input("Enter Patient Email:")
    appointment_date = st.date_input("Select Appointment Date")

    if st.button("Book Appointment"):
        result = book_appointment(patient_id, appointment_date.strftime("%Y-%m-%d"), patient_email)
        st.success(result)

elif choice == "Reminders":
    st.header("📢 Send Appointment Reminders")
    if st.button("Send Reminder Emails"):
        send_reminders()




elif main_menu == "Employee Management":
    emp_menu = ["Register Employee", "View Employee Details & Download PDF"]
    emp_choice = st.sidebar.selectbox("📁 Employee Management Menu", emp_menu)

    if emp_choice == "Register Employee":
        st.subheader("📝 Register New Employee")
        employee_id = generate_employee_id()
        st.write(f"**Next Employee ID:** {employee_id}")

        full_name = st.text_input("Full Name")
        department = st.selectbox("Department", ["HR", "Technical & Support Staff", "Emergency & Surgical Staff", "Finance",
                                   "Nursing", "Pharmacy", "Administration"])
        role = st.selectbox("Role", ["Manager", "Technician", "Nurse", "Doctor", "Receptionist", "Medical Equipment Technician",
                             "Accountant", "Pharmacist"])
        contact = st.text_input("Contact")
        email = st.text_input("Email")
        salary = st.number_input("Salary", min_value=0.0, step=1000.0)
        join_date = st.date_input("Joining Date")
        shift = st.selectbox("Shift", ["Morning", "Evening", "Night"])
        status = st.selectbox("Status", ["Active", "Inactive"])

        if st.button("➕ Add Employee"):
            add_employee(full_name, department, role, contact, email, salary, join_date, shift, status)

    elif emp_choice == "View Employee Details & Download PDF":
        employee_id = st.text_input("Enter Employee ID")
        if st.button("Get Details"):
            if employee_id.strip() == "":
                st.warning("⚠️ Please enter a valid Employee ID.")
            else:
                employee_data = get_employee_details(employee_id)

                if employee_data is not None:
                    st.success("✅ Employee Found!")

                    # Display Details
                    st.write(f"**Full Name:** {employee_data['FullName']}")
                    st.write(f"**Department:** {employee_data['Department']}")
                    st.write(f"**Role:** {employee_data['Role']}")
                    st.write(f"**Contact:** {employee_data['Contact']}")
                    st.write(f"**Email:** {employee_data['Email']}")
                    st.write(f"**Salary:** ${employee_data['Salary']}")
                    st.write(f"**Joining Date:** {employee_data['JoinDate']}")
                    st.write(f"**Shift:** {employee_data['Shift']}")
                    st.write(f"**Status:** {employee_data['Status']}")

                    # Generate PDF
                    pdf_path = generate_employee_pdf(employee_data)

                    # Provide PDF Download Button
                    with open(pdf_path, "rb") as pdf_file:
                        st.download_button(
                            label="📄 Download Employee Report (PDF)",
                            data=pdf_file,
                            file_name=f"Employee_{employee_id}.pdf",
                            mime="application/pdf"
                        )

                else:
                    st.error("❌ Employee Not Found!")


