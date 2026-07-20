from werkzeug.security import generate_password_hash, check_password_hash

from dao import users_dao


#Returns user with given id 
def get_user(user_id):
    return users_dao.get_user_by_id(user_id)

#Registers a new user
#Checks if the username exists
#Hashes the password

#other requirements checked at one layer above at app.py in order to increase performance
def register_user(username, password,role):

    if users_dao.get_user_by_username(username) is not None:
        return None, "That codename is already taken."

    new_id = users_dao.create_user(
        username, generate_password_hash(password), role)
    if new_id is None:
        return None, "Could not create the account, please try again."
    return new_id, None

#return user row if username and password is correct
def verify_login(username, password):

    row = users_dao.get_user_by_username(username)
    if row is None:
        return None
    if not check_password_hash(row["password_hash"], password):
        return None
    return row