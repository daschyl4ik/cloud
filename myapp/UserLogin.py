# class UserLogin():
#     #метод используется при создании объекта в load_user, 
#     #чтобы наполнить экземпляр класса UserLogin данными конкретного юзера
#     #формируем св-во __гыук и присваиваем ему то, что получаем с помощью getUser
#     #getUser берет данные из бд
#     # def fromDB(self, user_id, db):
#     #     self.__user = db.getUser(user_id)
#     #     return self
    
#     def fromDB(self, user_id, db):
#         self.__user = Users.query.filter_by(self.user_id).first()
#         return self


#     #передаем полученную информацию экземпляру класса.
#     #т.е. эти два метода формируют св-во __user, 
#     #которое позволяет нам получить айди и идент-ть юзера
#     def create(self, user):
#         self.__user = user
#         return self

#     def is_authenticated(self):
#         return True
    
#     def is_active(self):
#         return True
    
#     def is_anonymous(self):
#         return False
    
#     def get_id(self):
#         return str(self.__user["id"])