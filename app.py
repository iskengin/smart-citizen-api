import json

from flask import Flask,jsonify,abort,make_response,request
from flaskext.mysql import MySQL
app = Flask(__name__)

mysql = MySQL()
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'mustafaengin'
app.config['MYSQL_DATABASE_DB'] = 'smart'
app.config['MYSQL_DATABASE_HOST'] = '127.0.0.1'
app.config['MYSQL_DATABASE_CHARSET'] = 'utf8'
mysql.init_app(app)

keysForLogin = ['email','password']
keysForRegister = ['fullname','email','password']
keysForReport = ['email','password','neighborhood','longitude','latitude','locationDetail','title','description','category','imageUrl']

def check_auth_for_modules(email,password):
    conn = mysql.connect()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM User WHERE USR_email ='%s'" % (email))
    r = [dict((cursor.description[i][0], value) \
               for i, value in enumerate(row)) for row in cursor.fetchall()]

    if r:
        cursor.execute("SELECT USR_name as fullname, USR_email as email \
         FROM User WHERE USR_email ='%s' and USR_password='%s' " % (email,password))
        r = [dict((cursor.description[i][0], value) \
               for i, value in enumerate(row)) for row in cursor.fetchall()]
        cursor.connection.close()
        if r:
            return 1
        else:
            return 2 #password incorrect
    else:
        cursor.connection.close()
        return 3 #email incorrect


def check_auth(email,password):
    conn = mysql.connect()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM User WHERE USR_email ='%s'" % (email))
    r = [dict((cursor.description[i][0], value) \
               for i, value in enumerate(row)) for row in cursor.fetchall()]

    if r:
        cursor.execute("Select USR_name as fullname, USR_email as email, \
            Institution.`INS_id` as institution from User,Institution\
            where User.`USR_institution` = Institution.`INS_id` and \
            USR_email ='%s' and USR_password='%s' " % (email,password))
        r = [dict((cursor.description[i][0], value) \
               for i, value in enumerate(row)) for row in cursor.fetchall()]
        cursor.connection.close()
        if r:
            result = {'data' : r[0], 'serviceCode' : 0, 'exception': None}
            return jsonify(result)
        else:
            return jsonify({'serviceCode': 1, 'data': None , 'exception': {'exceptionCode':1, 'exceptionMessage':'The password is incorrect'}})
    else:
        cursor.connection.close()
        return jsonify({'serviceCode': 1, 'data': None , 'exception': {'exceptionCode':2, 'exceptionMessage':'There is no user with email '+email}})

def get_report_details_for_modules(reportID):
    reportId = reportID
    conn = mysql.connect()
    cursor = conn.cursor()

    if reportId == None:
        
        jsonMessage = {'serviceCode' : 1, 'data':None, 'exception':{'exceptionCode': 4, 'exceptionMessage': 'There is no reportId parameter'}}

    else:
        cursor.execute("Select Problem.PRB_id as problemId, User.`USR_name` as fullname, Problem.`PRB_title` as title, Category.`CAT_name` as category,\
            Problem.`PRB_explanation` as description, ProblemState.`PRS_name` as state, City.`CTY_name` as city ,District.`DST_name` as district, \
            Neighborhood.`NBH_name` as neighborhood, Location.`LOC_latitude` as latitude, Location.`LOC_longitude` as longitude, \
            Problem.`PRB_authorizedUser` as authorizedUser, DATE_FORMAT(Problem.`PRB_createdDate`, '%%d-%%m-%%Y')  as createdDate, \
            DATE_FORMAT(Problem.`PRB_updatedDate`, '%%d-%%m-%%Y')  as updatedDate, ProblemImage.PRI_imageUrl as imageUrl \
            from Problem, Category, User, ProblemState, Location, Neighborhood, District, city, ProblemImage \
            WHERE Problem.`PRB_category` = Category.`CAT_id` and Problem.`PRB_reportingUser` = User.`USR_id` and Problem.`PRB_state` = ProblemState.`PRS_id` and \
            Problem.`PRB_location` = Location.`LOC_id` and Location.`LOC_neighborhood` = Neighborhood.`NBH_id` and Neighborhood.`NBH_district` = District.`DST_id` and\
            District.`DST_city` = City.`CTY_id` and Problem.`PRB_id` = ProblemImage.`PRI_problem` and Problem.`PRB_id` = '%s'" % (reportId))
        reports = [dict((cursor.description[i][0], value) \
               for i, value in enumerate(row)) for row in cursor.fetchall()]
        if reports:
            jsonMessage = {'serviceCode':0, 'data': reports, 'exception': None}
        else:
            jsonMessage = {'serviceCode':1, 'data': None, 'exception': {'exceptionCode': 5, 'exceptionMessage': 'There is no report for this reportID'}}

    cursor.connection.close()
    return jsonify(jsonMessage)


@app.route('/api/memberLogin', methods=['POST'])
def memberLogin():
    if not request.json:
        abort(400)
    for key in keysForLogin:
        if not key in request.json:
            abort(400)

    result = check_auth(request.json['email'],request.json['password'])
    return result


@app.route('/api/memberSignUp', methods=['POST'])
def register():
    if not request.json:
        abort(400)
    for key in keysForRegister:
        if not key in request.json:
            abort(400)

    conn = mysql.connect()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM User WHERE USR_email ='%s'" % (request.json['email']))
    r = [dict((cursor.description[i][0], value) \
               for i, value in enumerate(row)) for row in cursor.fetchall()]
    if r:
        return jsonify({'serviceCode':1, 'data': None, 'exception':{'exceptionCode':3, 'exceptionMessage':'This e-mail has already been registered'}})
    else:
        cursor.execute("INSERT INTO User (USR_email,USR_name,USR_password,USR_institution) \
            VALUES ('%s','%s','%s',0);" % (request.json['email'],request.json['fullname'], request.json['password']))
        
        conn.commit()
        result = check_auth(request.json['email'],request.json['password'])
        #id = cursor.lastrowid
        cursor.connection.close()
        return result


@app.route('/api/sendReport', methods=['POST'])
def sendReport():
    if not request.json:
        abort(400)
    for key in keysForReport:
        if not key in request.json:
            abort(400)

    conn = mysql.connect()
    cursor = conn.cursor()

    cursor.execute("SELECT USR_id FROM User WHERE USR_email ='%s' and USR_password ='%s'" % (request.json['email'],request.json['password']))
    result = [dict((cursor.description[i][0], value) \
               for i, value in enumerate(row)) for row in cursor.fetchall()]
    if result:
        userid = result[0]['USR_id']
        cursor.execute("INSERT INTO Location (LOC_latitude,LOC_longitude,LOC_detail,LOC_neighborhood) \
            VALUES ('%f','%f','%s',1);" % (request.json['latitude'],request.json['longitude'], request.json['locationDetail']))
        conn.commit()
        locationId = cursor.lastrowid

        cursor.execute("INSERT INTO Problem (PRB_category,PRB_location,PRB_state,PRB_title, PRB_explanation,PRB_reportingUser, PRB_createdDate) \
            VALUES ('%d','%d',1,'%s','%s','%d',CURDATE());" % (request.json['category'],locationId,request.json['title'],request.json['description'],userid))
        conn.commit()
        problemid = cursor.lastrowid

        cursor.execute("INSERT INTO ProblemImage (PRI_problem,PRI_imageUrl) \
            VALUES ('%d','%s');" % (problemid,request.json['imageUrl']))
        conn.commit()
        cursor.connection.close()
        jsonMessage = get_report_details_for_modules(problemid)
        return jsonMessage
    else:
        cursor.connection.close()
        jsonMessage = {'serviceCode': 1, 'data': None, 'exception':{'exceptionCode':7,'exceptionMessage':'E-mail or password incorrect'}}
        return jsonify(jsonMessage)   


@app.route('/api/getReportsOnMap', methods=['GET'])
def getOnReportsOnMap():
    reportType = request.args.get('reportType')
    conn = mysql.connect()
    cursor = conn.cursor()

    if reportType == "0" or reportType == None:
        cursor.execute("Select Problem.`PRB_id` as id, Category.`CAT_name` as reportType, Problem.`PRB_title` as title, Problem.`PRB_explanation` as description,\
            Location.`LOC_latitude` as latitude, Location.`LOC_longitude` as longitude from Problem, Location, Category\
            where Problem.`PRB_location` = Location.`LOC_id` and Problem.`PRB_category` = Category.`CAT_id`")
        reports = [dict((cursor.description[i][0], value) \
               for i, value in enumerate(row)) for row in cursor.fetchall()]
        jsonMessage = {'serviceCode':0, 'data': reports, 'exception': None}

    else:
        cursor.execute("Select Problem.`PRB_id` as id, Category.`CAT_name` as reportType, Problem.`PRB_title` as title, Problem.`PRB_explanation` as description, \
            Location.`LOC_latitude` as latitude, Location.`LOC_longitude` as longitude from Problem, Location, Category \
            where Problem.`PRB_location` = Location.`LOC_id` and Problem.`PRB_category` = Category.`CAT_id` and Problem.`PRB_category` = '%s'" % (reportType))
        reports = [dict((cursor.description[i][0], value) \
               for i, value in enumerate(row)) for row in cursor.fetchall()]
        if reports:
            jsonMessage = {'serviceCode':0, 'data': reports, 'exception': None}
        else:
            jsonMessage = {'serviceCode':1, 'data': None, 'exception': {'exceptionCode': 6, 'exceptionMessage': 'There is no report for this reportType'}}

    cursor.connection.close()
    return jsonify(jsonMessage)


@app.route('/api/getReportDetails', methods=['GET'])
def getReportDetails():
    reportId = request.args.get('reportId')
    conn = mysql.connect()
    cursor = conn.cursor()

    if reportId == None:
        
        jsonMessage = {'serviceCode' : 1, 'data':None, 'exception':{'exceptionCode': 4, 'exceptionMessage': 'There is no reportId parameter'}}

    else:
        cursor.execute("Select Problem.PRB_id as problemId, User.`USR_name` as fullname, Problem.`PRB_title` as title, Category.`CAT_name` as category,\
            Problem.`PRB_explanation` as description, ProblemState.`PRS_name` as state, City.`CTY_name` as city ,District.`DST_name` as district, \
            Neighborhood.`NBH_name` as neighborhood, Location.`LOC_latitude` as latitude, Location.`LOC_longitude` as longitude, \
            Problem.`PRB_authorizedUser` as authorizedUser, DATE_FORMAT(Problem.`PRB_createdDate`, '%%d-%%m-%%Y')  as createdDate, \
            DATE_FORMAT(Problem.`PRB_updatedDate`, '%%d-%%m-%%Y')  as updatedDate, ProblemImage.PRI_imageUrl as imageUrl \
            from Problem, Category, User, ProblemState, Location, Neighborhood, District, city, ProblemImage \
            WHERE Problem.`PRB_category` = Category.`CAT_id` and Problem.`PRB_reportingUser` = User.`USR_id` and Problem.`PRB_state` = ProblemState.`PRS_id` and \
            Problem.`PRB_location` = Location.`LOC_id` and Location.`LOC_neighborhood` = Neighborhood.`NBH_id` and Neighborhood.`NBH_district` = District.`DST_id` and\
            District.`DST_city` = City.`CTY_id` and Problem.`PRB_id` = ProblemImage.`PRI_problem` and Problem.`PRB_id` = '%s'" % (reportId))
        reports = [dict((cursor.description[i][0], value) \
               for i, value in enumerate(row)) for row in cursor.fetchall()]
        if reports:
            jsonMessage = {'serviceCode':0, 'data': reports, 'exception': None}
        else:
            jsonMessage = {'serviceCode':1, 'data': None, 'exception': {'exceptionCode': 5, 'exceptionMessage': 'There is no report for this reportID'}}

    cursor.connection.close()
    return jsonify(jsonMessage)



@app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify({'serviceCode': 1, 'data': None, 'exception':{'exceptionCode':400, 'exceptionMessage': 'Bad request'}}),400)

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'serviceCode': 1, 'data': None, 'exception':{'exceptionCode':404, 'exceptionMessage': 'Not found'}}),404)

@app.errorhandler(405)
def not_found(error):
    return make_response(jsonify({'serviceCode': 1, 'data': None, 'exception':{'exceptionCode':405, 'exceptionMessage': 'Method not allowed'}}),405)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port = 80 ,debug=True)
    #host='0.0.0.0',

