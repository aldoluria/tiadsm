from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import UserMixin

class User(UserMixin):

    def get_id(self):
        return(self.idusuarios)

    def __init__(self,idusuarios, username, password, tipo) -> None:
        self.idusuarios=idusuarios
        self.username=username
        self.password=password
        self.tipo=tipo

    @classmethod
    def check_password(self, hashed_password, password):
        return check_password_hash(hashed_password, password)

#print(generate_password_hash("1234"))