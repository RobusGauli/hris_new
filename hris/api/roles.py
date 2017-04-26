'''This module is responsbile for creating roles and assigning different permissions to the roles'''
from hris.utils import hash_password, gen_access_token, decode_access_token, random_string
from flask import request, abort, jsonify, g, current_app
from functools import wraps
import copy
from hris.utils import (
    handle_keys_for_post_request,
    handle_keys_for_update_request
)

from hris.api import api
from sqlalchemy.exc import IntegrityError #foreign key violation #this won't come up oftern
from sqlalchemy.orm.exc import NoResultFound
from hris import db_session, engine

#auth
from hris.api.auth import (
    create_update_permission,
    read_permission
)
###
from hris.models import (
    User, 
    CompanyDetail, 
    Role
)
from functools import wraps

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
    extra_keys_envelop,
    keys_require_envelop
)


def update_query(table_name,mapping, id):
    inner = ', '.join('{:s} = {!r}'.format(key, val) for key, val in mapping)
    query = '''UPDATE {} SET {:s} where id = {:d}'''.format(table_name, inner, id)
    return query




@api.route('/roles', methods = ['POST'])
@create_update_permission('user_management_perm')
@handle_keys_for_post_request(Role, _exclude=('id', 'updated_at', 'updated_by', 'created_at', 'created_by', 'del_flag', 'permission_eight', 'permission_nine', 'permission_ten', 'role_type_display_name'))
def create_roles():
    '''This method will create a role and assign diffenet permissions'''
    try:
         json_request = dict(copy.deepcopy(request.json))
         json_request['role_type_display_name'] = request.json.get('role_type')
         role = Role(**json_request)
         db_session.add(role)
         db_session.commit()
    except IntegrityError as e:
        return record_exists_envelop()
    except Exception as e:
        raise
        return fatal_error_envelop()
    else:
        
        return record_created_envelop(request.json)

@api.route('/roles', methods=['GET'])
@read_permission('read_management_perm')
def get_roles():
    try:
        roles = db_session.query(Role).all()
    except NoResultFound as e:
        return record_notfound_envelop()
    except Exception as e:
        return fatal_error_envelop()
    else:
        return records_json_envelop(list(role.to_dict() for role in roles))




@api.route('/roles/<int:r_id>', methods=['PUT'])
@create_update_permission('user_management_perm')
@handle_keys_for_update_request(Role, _exclude=('id', ))
def update_role(r_id):
    #check to see if they want to update the admin_role. refuse to change the admin_roel
    

    #clean up the json values
    cleaned_json = ((key, val.strip()) if isinstance(val, str) else (key, val) for key, val in request.json.items())

    query = update_query(Role.__tablename__, cleaned_json, r_id)

    with engine.connect() as con:
        try:
            con.execute(query)
        except IntegrityError as e:
            return record_exists_envelop() 
        except Exception as e:
            return fatal_error_envelop()
        else:
            roles = db_session.query(Role).all()
            roles = [role.to_dict() for role in roles]
            for role in roles:
                current_app.config[role['id']]= role
            return record_updated_envelop(request.json)



@api.route('/roles/<int:r_id>', methods = ['GET'])
@read_permission('read_management_perm')
def get_role_by_id(r_id):
    try:
        role = db_session.query(Role).filter(Role.id==r_id).one()
    except NoResultFound as e:
        return record_notfound_envelop()
    except Exception as e:
        return fatal_error_envelop()
    else:
        return record_json_envelop(role.to_dict())


    