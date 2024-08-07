from .entities.user import User

class ModuleUser():
    @classmethod
    def login(self, db, user):
        try:
            cur=db.cursor()
            sql="SELECT id_usuario, username, password FROM usuarios WHERE activo='true' and username='{}'".format(user.username)
            cur.execute(sql)
            row=cur.fetchone()
            if row != None:
                user=User(row[0],row[1],user.check_password(row[2],user.password),None,None,None,None)
                return user
            else:
                return None
        except Exception as ex:
            raise Exception(ex)

    @classmethod
    def get_by_id(self, db, id_usuario):
        try:
            cur=db.cursor()
            sql="SELECT U.id_usuario, U.username, T.nombre, U.activo, U.creado, U.editado FROM usuarios AS U INNER JOIN tipos_usuarios AS T ON U.id_tipo = T.id_tipo WHERE U.activo='true' and U.id_usuario='{}'".format(id_usuario)
            cur.execute(sql)
            row=cur.fetchone()
            if row != None:
                return User(row[0], row[1], None, row[2], row[3], row[4], row[5])
            else:
                return None
        except Exception as ex:
            raise Exception(ex)