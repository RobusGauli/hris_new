import time
import hashlib
from functools import wraps
from flask import request, jsonify

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
    Training,
    Role
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
    extra_keys_envelop,
    unauthorized_envelop,
    keys_require_envelop
)



import jwt

SECRET = 'shivapandeyisverybad'

STRINGS = 'ABCSJKSHDJHG'
from random import choice

def random_string(num):
    return ''.join(choice(STRINGS) for i in range(num))
    

def timestamp():
    return int(time.time())

def hash_password(password):
    if isinstance(password, str):
        password = password.encode()
    return hashlib.sha256(password).hexdigest()
    


def gen_access_token(role_id, user_name, issuer='drose.com.np'):
    payload = {'role_id' : role_id, 'user_name': user_name, 'iss': issuer}

    encoded = jwt.encode(payload, SECRET, algorithm='HS256')
    return encoded

def decode_access_token(encoded):
    decoded = None
    try:

        decoded = jwt.decode(encoded, SECRET, algorithms=['HS256'])

    except jwt.DecodeError as e:
        pass
    else:
        return decoded

#simple decorator function to allow access to the endpoint
#useless function that can be deleted
def can_edit_permit(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        #check if there is access_token in the headers
        if not 'Token' in request.headers.keys():
            return jsonify({'message': 'not_authorized', 'code': '401'})
        #try decoding the token
        decoded = decode_access_token(request.headers['token'])
        if not decoded:
            return jsonify({'message': 'not authorized', 'code': '401'})
        
        if decoded['role_id'] == 1:
            return func(*args, **kwargs)
        else:
            return jsonify({'message' : 'not authorized', 'code' : '401'})

    return wrapper



def handle_keys_for_post_request(model, *, _exclude=None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            fields_db = set(col.name for col in model.__mapper__.columns)
            if not request.json:
                abort(400)
            required_keys = fields_db - set(_exclude) if _exclude else set()
            result = request.json.keys() - required_keys
            if result:
                return extra_keys_envelop('Keys not Accepeted %r' % (', '.join(key for key in result)))
            #check if there are any missing keys
            result = required_keys - request.json.keys()
            if result:
                return keys_require_envelop('Keys required %r' %(' ,'.join(key for key  in result)))
            #check if there are any fields emopty
            if not all(len(str(val).strip()) >= 2 for val in request.json.values()):
                return length_require_envelop()
            #everythin is okay return the function
            return func(*args, **kwargs)
        return wrapper
    return decorator



def handle_keys_for_update_request(model, *, _exclude=None):
    def _decorator(func):
        @wraps(func)
        def _wrapper(*args, **kwargs):

            fields_db = set(col.name for col in model.__mapper__.columns)
            if not request.json:
                abort(400)
            required_keys = fields_db - set(_exclude) if _exclude else set()
            result = request.json.keys() - required_keys
            if result:
                return extra_keys_envelop('Keys not Accepeted %r' % (', '.join(key for key in result)))
            #check if there are any missing keys
            
            if not all(len(str(val).strip()) >= 1 for val in request.json.values()):
                return length_require_envelop()
            #everythin is okay return the function
            return func(*args, **kwargs)
        return _wrapper
    return _decorator


