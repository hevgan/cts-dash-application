def health_check():
    from flask import  make_response
    return make_response({}, 200)