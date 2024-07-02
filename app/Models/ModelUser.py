from .entities.user import User

class ModuleUser():
    @classmethod
    def login(self, db, user):
        try:
            cur=db.cursor()
            sql="SELECT idusuarios, username, password FROM usuarios WHERE username='{}'".format(user.username)
            cur.execute(sql)
            row=cur.fetchone()
            if row != None:
                user=User(row[0],row[1],user.check_password(row[2],user.password),None)
                return user
            else:
                return None
        except Exception as ex:
            raise Exception(ex)

    @classmethod
    def get_by_id(self, db, idusuarios):
        try:
            cur=db.cursor()
            sql="SELECT idusuarios, username, tipo FROM usuarios WHERE idusuarios='{}'".format(idusuarios)
            cur.execute(sql)
            row=cur.fetchone()
            if row != None:
                return User(row[0], row[1], None, row[2])
            else:
                return None
        except Exception as ex:
            raise Exception(ex)