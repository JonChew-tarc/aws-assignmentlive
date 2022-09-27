from flask import Flask, render_template, request
from pymysql import connections
import os
from datetime import datetime
import boto3
from config import *

app = Flask(__name__)

bucket = custombucket
region = customregion
# Global Variables #
s3 = boto3.resource('s3')
s3_client = boto3.client('s3')
allow_image = set(['png', 'jpg', 'jpeg', 'gif'])

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

@app.route("/addemp/", methods=['GET', 'POST'])
def addEmpPage():
    sql_query = "SELECT * FROM employee"
    cursor = db_conn.cursor()
    try: 
        cursor.execute(sql_query)
        records = cursor.fetchall()
        emp_id = employee_id + int(len(records))
        cursor.close()

        return render_template('AddEmp.html',date=datetime.now(), emp_id = emp_id)
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
    cursor = db_conn.cursor()

    if emp_image_file.filename == "":
        return "Please select a file"

    try:

        cursor.execute(insert_sql, (emp_id, first_name, last_name, training, email))
        db_conn.commit()
        emp_name = "" + first_name + " " + last_name
        # Uplaod image file in S3 #
        emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + "_image_file"
        s3 = boto3.resource('s3')

        try:
            print("Data inserted in MySQL RDS... uploading image to S3...")
            s3.Bucket(custombucket).put_object(Key=emp_image_file_name_in_s3, Body=emp_image_file)
            bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
            s3_location = (bucket_location['LocationConstraint'])

            if s3_location is None:
                s3_location = ''
            else:
                s3_location = '-' + s3_location

            object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                s3_location,
                custombucket,
                emp_image_file_name_in_s3)

        except Exception as e:
            return str(e)

    finally:
        cursor.close()

    print("all modification done...")
    return render_template('AddEmpOutput.html', name=emp_name)

@app.route("/getemp/")
def getEmp():
    return render_template('GetEmp.html')

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
    

     return render_template("GetEmpOutput.html",result=result)

@app.route("/applyLeave", methods = ['POST'])
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

@app.route("/deleteEmp", methods=["post"])
def deleteEmp():
    emp_id = request.form['emp_id']
    delete_emp = "DELETE FROM employee WHERE emp_id = %(emp_id)s"
    cursor = db_conn.cursor()

    try:
        cursor.execute(delete_emp)
        db_conn.commit()
    except Exception as e:
            return str(e)
    finally:
        cursor.close() 

    return render_template("Homepage.html")

@app.route("/backHome", methods=['POST'])
def backHome():
    return render_template("Homepage.html")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)