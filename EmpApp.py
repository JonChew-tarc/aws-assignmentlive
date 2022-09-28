from flask import Flask, render_template, request
from pymysql import connections
from datetime import datetime
import os
import boto3
from config import *

app = Flask(__name__)

bucket = custombucket
region = customregion

db_conn = connections.Connection(
    host=customhost,
    port=3306,
    user=customuser,
    password=custompass,
    db=customdb

)
output = {}
table = 'employee'
employee_id = 1001
s3 = boto3.resource('s3')
s3_client = boto3.client('s3')


@app.route("/addemp", methods=['GET', 'POST'])
def addEmpPage():
    sql_query = "SELECT * FROM employee"
    cursor = db_conn.cursor()
    try: 
        cursor.execute(sql_query)
        records = cursor.fetchall()
        emp_id = employee_id + int(len(records))
        cursor.close()
        return render_template('AddEmp.html', date=datetime.now(), empId = emp_id)
    except Exception as e:
        return str(e)
    

@app.route("/")
def home():
    sql_query = "SELECT * FROM employee"
    cursor = db_conn.cursor()
    try: 
        cursor.execute(sql_query)
        records = cursor.fetchall()
        emp_id = employee_id + int(len(records))
        cursor.close()
        return render_template('AddEmp.html', date=datetime.now(), empId = emp_id)
    except Exception as e:
        return str(e)



@app.route("/addemp/results", methods=['POST'])
def AddEmp():
    emp_id = request.form['emp_id']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    training = request.form['training']
    email = request.form['email']
    emp_image_file = request.files['emp_image_file']

    insert_sql = "INSERT INTO employee VALUES (%s, %s, %s, %s, %s)"
    insertAtt_sql = "INSERT INTO attendance VALUES (%s, %s)"
    cursor = db_conn.cursor()

    if emp_image_file.filename == "":
        return "Please select a file"

    try:

        cursor.execute(insert_sql, (emp_id, first_name, last_name, training, email))
        cursor.execute(insertAtt_sql, (emp_id, "Out"))
        db_conn.commit()
        emp_name = "" + first_name + " " + last_name
        # Uplaod image file in S3 #
        emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + "_image_file"
        #s3 = boto3.resource('s3')

        try:
            print("Data inserted in MySQL RDS... uploading image to S3...")
            s3.Bucket(custombucket).put_object(Key=emp_image_file_name_in_s3, Body=emp_image_file)
            bucket_location = s3_client.get_bucket_location(Bucket=custombucket)
            s3_location = (bucket_location['LocationConstraint'])

            if s3_location is None:
                s3_location = ''
            else:
                s3_location = '-' + s3_location

            object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                s3_location,
                custombucket,
                emp_image_file_name_in_s3)
            
            profilePicList = []

            public_url = s3_client.generate_presigned_url('get_object', 
                                                        Params = {'Bucket': custombucket, 
                                                                    'Key': emp_image_file_name_in_s3})

            profilePicList.append(public_url)

        except Exception as e:
            return str(e)

    finally:
        cursor.close()

    print("all modification done...")
    return render_template('AddEmpOutput.html', date = datetime.now(), empName = emp_name, profilePicList = profilePicList)

@app.route("/getemp/")
def getEmp():
    return render_template('GetEmp.html', date=datetime.now())

@app.route("/getemp/results",methods=['GET','POST'])
def Employee():
    
     #Get Employee
     emp_id = request.form['emp_id']
    # SELECT STATEMENT TO GET DATA FROM MYSQL
     current_emp = "SELECT * FROM employee WHERE emp_id = %(emp_id)s"

     
     cursor = db_conn.cursor()
        
     try:
         cursor.execute(current_emp, { 'emp_id': int(emp_id) })
         # #FETCH ONLY ONE ROWS OUTPUT
         for result in cursor:
            print(result)
        

     except Exception as e:
        return str(e)
        
     finally:
        cursor.close()
    

     return render_template("GetEmpOutput.html",result=result, date=datetime.now())

@app.route("/leave")
def getLeave():
    return render_template('LeaveEmp.html', date=datetime.now())

#ROUTE TO PAYROLL
@app.route("/payroll")
def getPayroll():
    return render_template("Payroll.html", date=datetime.now())

#ROUTE TO HOMEPAGE
@app.route("/homepage")
def getHomepage():
    return render_template("Homepage.html", date=datetime.now())


@app.route("/applyLeave", methods=['POST'])
def applyLeave():
    #let user pick the calendar
    #add into the database
    #show feedback message (from invisible to visible [label])
    emp_id = request.form['emp_id'] #i think this is session, need this session to identify which employee
    dateOfLeaveStart = request.form['leaveStartDate']
    dateOfLeaveEnd = request.form['leaveEndDate']
    leaveReason = request.form['leaveReason']
    leaveEvidence = request.files['supportingDocument']
    
    
    insert_sql = "INSERT INTO leaveEmployee VALUES (%s, %s, %s, %s)"
    select_emp = "SELECT emp_id FROM employee WHERE emp_id = %(emp_id)s"
    cursor = db_conn.cursor()

    try:
        #cursor.execute(select_emp,{'emp_id':int(emp_id)}) #not sure need this or not
        cursor.execute(insert_sql, (dateOfLeaveStart, dateOfLeaveEnd, leaveReason, emp_id))
        db_conn.commit()
        emp_leave_file_name_in_s3 = "emp-leave-" + str(dateOfLeaveStart) + "_image_file"
        s3 = boto3.resource('s3')
        try:
            print("Data inserted in MySQL RDS... uploading image to S3...")
            s3.Bucket(custombucket).put_object(Key=emp_leave_file_name_in_s3, Body=leaveEvidence)
            bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
            s3_location = (bucket_location['LocationConstraint'])

            if s3_location is None:
                s3_location = ''
            else:
                s3_location = '-' + s3_location

            object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                s3_location,
                custombucket,
                emp_leave_file_name_in_s3)

        except Exception as e:
            return str(e)

    finally:
        cursor.close() 

    print("all modification done...") 
    return render_template("AddEmp.html")  

@app.route("/backHome", methods=['POST'])
def backHome():
    return render_template("Homepage.html")

@app.route("/attendance", methods=['GET','POST'])
def getAttendancePage():
    select_sql = "SELECT e.emp_id, e.first_name, e.last_name, a.attend FROM employee e, attendance a WHERE e.emp_id = a.emp_id"
    cursor = db_conn.cursor()
    cursor.execute(select_sql)
    db_conn.commit()
    result = cursor.fetchall()

    arr = []
    for col in range(len(result)):
        arr.append([])
        arr[col].append(result[col][0] )
        arr[col].append(str(result[col][1]) + " " + str(result[col][2]))
        arr[col].append(result[col][3])

    cursor.close()

    return render_template("Attendance.html", date=datetime.now(), tableContent = arr)

@app.route("/attendance/output", methods=['GET', 'POST'])
def notifyAttendancePage():
    emp_id = request.form['emp_id']
    cursor1 = db_conn.cursor()
    cursor2 = db_conn.cursor()
    cursor3 = db_conn.cursor()
    cursor4 = db_conn.cursor()
    
    
    get_status = "SELECT attend FROM attendance WHERE emp_id = %s"
    get_firstname = "SELECT first_name FROM employee WHERE emp_id = %s"
    get_lastname = "SELECT last_name FROM employee WHERE emp_id = %s"
    check_attendance = "UPDATE attendance SET attend = %s WHERE emp_id = %s"
    
    try:
        cursor1.execute(get_status,(emp_id))
        cursor2.execute(get_firstname,(emp_id))
        cursor3.execute(get_lastname,(emp_id))
        db_conn.commit()
        
    except Exception as e:
        return str(e)

    result = str(cursor1.fetchone())
    firstname = str(cursor2.fetchone())
    lastname = str(cursor3.fetchone())
    resultOutput = ""
    try:
        if(result == "In"):
            cursor4.execute(check_attendance,("Out", emp_id))
            resultOutput = "Checked Out"
        else:
            cursor4.execute(check_attendance,("In", emp_id))
            resultOutput = "Checked In"
        db_conn.commit()
    except Exception as e:
        return str(e)
    
    cursor1.close() 
    cursor2.close() 
    cursor3.close() 
    cursor4.close() 
    print("all modification done...") 
    return render_template('AttendanceOutput.html', date = datetime.now(), empName = (firstname + " " + lastname), status = resultOutput)



@app.route("/deleteEmp", methods=['POST'])
def deleteEmp():
    emp_id = request.form['emp_id']
    delete_emp = "DELETE FROM employee WHERE emp_id = %s"
    delete_att = "DELETE FROM attendance WHERE emp_id = %s"
    cursor = db_conn.cursor()
    cursor2 = db_conn.cursor()

    try:
        cursor.execute(delete_emp,(emp_id))
        cursor2.execute(delete_att,(emp_id))
        db_conn.commit()
    except Exception as e:
        return str(e)
    finally:
        cursor.close() 
        cursor2.close() 

    print("all modification done...") 
    return render_template('Homepage.html', date=datetime.now())

#PAYROLL OUTPUT PAGE
@app.route("/payroll/results", methods=['GET','POST'])
def AddPayroll():
    emp_id = request.form['emp_id']
    working_hour = request.form['working_hour_per_day']
    monthly_salary = request.form['monthly_salary']
    annual_salary = request.form['annual_salary']

    insert_sql = "INSERT INTO employeeSalary VALUES (%s, %s, %s, %s)"
    cursor = db_conn.cursor()

    try:
        cursor.execute(insert_sql, (emp_id, working_hour, monthly_salary, annual_salary))
        db_conn.commit()

    except Exception as e:
        return str(e)

    finally:
        cursor.close()

    print("all modification done...")
    return render_template('Homepage.html', date=datetime.now())

#PAYROLL PAGE 
@app.route("/payroll/calculate",methods=['GET','POST'])
def CalpayRoll():

    emp_id = int(request.form.get('emp_id'))
    hourly_salary_rate = int(request.form.get('hourly_salary_rate'))
    working_hour_per_day = int(request.form.get('working_hour_per_day'))
    working_day_per_week = int(request.form.get('working_day_per_week'))

    monthly_salary = hourly_salary_rate*working_hour_per_day*working_day_per_week*4 
    annual_salary = monthly_salary*12

    return render_template('PayrollOutput.html',emp_id=emp_id, monthly_salary= monthly_salary , annual_salary = annual_salary, working_hour_per_day = working_hour_per_day, date=datetime.now())


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)