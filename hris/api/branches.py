from hris.utils import hash_password, gen_access_token, decode_access_token
from flask import request, abort, jsonify, g
from functools import wraps

from hris.api import api
from sqlalchemy.exc import IntegrityError #foreign key violation #this won't come up oftern
from sqlalchemy.orm.exc import NoResultFound
from hris import db_session, ROLES_PERMISSION, engine
import copy

#auth

###
#auth
from hris.utils import (
    handle_keys_for_update_request,
    handle_keys_for_post_request
)

from hris.api.auth import (
    allow_permission, 
    create_update_permission,
    read_permission
)
###
from hris.models import (
    User, 
    CompanyDetail,
    Branch,
    EmployeeCategoryRank,
    EmployeeCategory,
    EmployeeType,
    Employee,
    EmployeeExtra,
    Qualification,
    Certification,
    Training
)


from hris.api.response_envelop import (
    records_json_envelop,
    record_exists_envelop,
    record_json_envelop,
    record_created_envelop,
    record_notfound_envelop,
    record_updated_envelop,
    record_not_updated_env,
    fatal_error_envelop,
    missing_keys_envelop, 
    length_require_envelop,
    unauthorized_envelop,
    extra_keys_envelop, 
    keys_require_envelop
)






@api.route('/agencies', methods=['POST'])
@create_update_permission('agency_management_perm')
def create_agency():
    if not request.json:
        abort(400)
    
    if not set(request.json.keys()) == {
                                        'facility_name',
                                        'facility_type_id',
                                        'llg_id', 
                                        'district_id', 
                                        'province_id', 
                                        'region_id'}:
        abort(401)
    #try to store the branch

    #make sure all the fields are non-empty
    if any(len(str(val).strip()) == 0 for val in request.json.values()):
        abort(411)
    
    #clean up the json values
    
    facility_display_name = request.json['facility_name'].strip()
    facility_type_id = request.json['facility_type_id']
    llg_id = request.json['llg_id']
    district_id = request.json['district_id']
    province_id = request.json['province_id']
    region_id = request.json['region_id']
    facility_name = facility_display_name.replace(' ', '').lower().strip()
    ##

    try:
        branch = Branch(
                        facility_name=facility_name,
                        facility_display_name = facility_display_name,
                        is_branch = False, 
                        llg_id=llg_id,
                        district_id=district_id,
                        province_id=province_id,
                        region_id=region_id,
                        facility_type_id=facility_type_id)
        db_session.add(branch)
        db_session.commit()
    except IntegrityError as e:
        return record_exists_envelop()
    except Exception as e:
        abort(500)
    else:
        return record_created_envelop(request.json)


@api.route('/branches', methods=['POST'])
@create_update_permission('division_management_perm')
def create_branch():
    if not request.json:
        abort(400)
    
    if not set(request.json.keys()) == {
                                        'facility_name',
                                        'facility_type_id',
                                        'llg_id', 
                                        'district_id', 
                                        'province_id', 
                                        'region_id'}:
        abort(401)
    #try to store the branch

    #make sure all the fields are non-empty
    if any(len(str(val).strip()) == 0 for val in request.json.values()):
        abort(411)
    
    #clean up the json values
    facility_display_name = request.json['facility_name'].strip()
    facility_name = facility_display_name.replace(' ', '').lower().strip()
    facility_type_id = request.json['facility_type_id']
    llg_id = request.json['llg_id']
    district_id = request.json['district_id']
    province_id = request.json['province_id']
    region_id = request.json['region_id']
    ##

    try:
        branch = Branch(is_branch=True,
                        facility_name=facility_name,
                        facility_display_name=facility_display_name, 
                        llg_id=llg_id,
                        district_id=district_id,
                        province_id=province_id,
                        region_id=region_id,
                        facility_type_id=facility_type_id)
        db_session.add(branch)
        db_session.commit()
    except IntegrityError as e:
        return record_exists_envelop()
    except Exception as e:
        abort(500)
    else:
        return record_created_envelop(request.json)
    



@api.route('/agencies/<int:a_id>', methods=['PUT'])
@create_update_permission('agency_management_perm')
def update_agency(a_id):

    #checck to see if there is json data
    if not request.json:
        abort(400)
    db_fields  = set(col.name for col in Branch.__mapper__.columns) - {'id', 'is_branch'}
    result = request.json.keys() - db_fields
    if result:
        return extra_keys_envelop('Keys not accepted %r' % (', '.join(key for key in result)))
    
    #now check if there are any missing values whose length is less than 2
    if not all(len(str(val).strip()) >=1 for val in request.json.values()):
        return length_require_envelop()
    
    json_request = dict(copy.deepcopy(request.json))
   
    facility_display_name = request.json.get('facility_name', None)
    if facility_display_name is not None:
        
        facility_name = facility_display_name.strip().replace(' ',  '').lower()
        json_request['facility_name'] = facility_name
        json_request['facility_display_name'] = facility_display_name.strip()
    
    inner = ', '.join('{:s} = {!r}'.format(key, val) for key, val in json_request.items())
    query = '''UPDATE branches SET {:s} where id = {:d}'''.format(inner, a_id)
    print(query)
    
    with engine.connect() as con:
        try:
            con.execute(query)
        except IntegrityError as e:
            return record_exists_envelop()
        except Exception as e:
            raise
            return fatal_error_envelop()
        else:
            return record_updated_envelop(json_request)
    
    

def handle_update_division_keys(model, *, exclude=None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not request.json:
                abort(400)
            
            db_fields = set(col.name for col in model.__mapper__.columns)
            required_fields = db_fields - set(exclude) if exclude is not None else set()

            result = request.json.keys() - required_fields
            if result:
                return extra_keys_envelop('Keys not accepted : {!r}'.format(',  '.join(key for key in result)))
            
            #now check if there are empty fields

            if not all(len(str(val).strip()) >=1 for val in request.json.values()):
                return length_require_envelop()

            #if everythin is fine then return the function
            return func(*args, **kwargs)
        return wrapper
    return decorator


@api.route('/branches/<int:d_id>', methods = ['PUT'])
@create_update_permission('division_management_perm')
@handle_update_division_keys(Branch, exclude={'id', 'is_branch'})
def update_division(d_id):

    json_request = dict(copy.deepcopy(request.json))
   
    facility_display_name = request.json.get('facility_name', None)
    if facility_display_name is not None:
        
        facility_name = facility_display_name.strip().replace(' ',  '').lower()
        json_request['facility_name'] = facility_name
        json_request['facility_display_name'] = facility_display_name.strip()
    
    inner = ', '.join('{:s} = {!r}'.format(key, val) for key, val in json_request.items())
    query = '''UPDATE branches SET {:s} where id = {:d}'''.format(inner, d_id)
    
    
    with engine.connect() as con:
        try:
            con.execute(query)
        except IntegrityError as e:
            return record_exists_envelop()
        except Exception as e:
            raise
            return fatal_error_envelop()
        else:
            return record_updated_envelop(json_request)
    

   





@api.route('/branches', methods=['GET'])
@read_permission('read_management_perm')
def get_branches():
    try:
        branches = db_session.query(Branch).filter(Branch.is_branch==True).filter(Branch.del_flag==False).filter(Branch.acitivate==True).order_by(Branch.facility_name).all()
        all_branches = (dict(id=branch.id,
                             facility_name=branch.facility_display_name,
                             llg=branch.llg.display_name,
                             district=branch.district.display_name,
                             province=branch.province.display_name,
                             region=branch.region.display_name,
                             facility_type=branch.facility_type.display_name,
                             ) for branch in branches)
    except Exception as e:
        return fatal_error_envelop()
    else:
        return records_json_envelop(list(all_branches))



@api.route('/agencies', methods=['GET'])
@read_permission('read_management_perm')
def get_agencies():
    try:
        branches = db_session.query(Branch).filter(Branch.is_branch==False).filter(Branch.del_flag==False).filter(Branch.acitivate==True).order_by(Branch.facility_name).all()
        all_branches = (dict(id=branch.id,
                             facility_name=branch.facility_display_name,
                             llg=branch.llg.display_name,
                             district=branch.district.display_name,
                             province=branch.province.display_name,
                             region=branch.region.display_name,
                             facility_type=branch.facility_type.display_name) for branch in branches)
    except Exception as e:
        return fatal_error_envelop()
    else:
        return records_json_envelop(list(all_branches))



@api.route('/branches/<int:b_id>/employees')
@read_permission('read_management_perm')
def get_employees_by_branch(b_id):
    try:
        employees = db_session.query(Employee).filter(Employee.employee_branch_id==b_id).filter(Employee.is_branch==True).all()
    except NoResultFound as e:
        return record_notfound_envelop()
    except Exception as e:
        return fatal_error_envelop()
    else:
        return records_json_envelop(list(emp.to_dict() for emp in employees))



@api.route('/agencies/<int:a_id>/employees')
@read_permission('read_management_perm')
def get_employees_by_agency(a_id):
    try:
        employees = db_session.query(Employee).filter(Employee.employee_branch_id==a_id).filter(Employee.is_branch==False).all()
    except NoResultFound as e:
        return record_notfound_envelop()
    except Exception as e:
        return fatal_error_envelop()
    else:
        return records_json_envelop(list(emp.to_dict() for emp in employees))


