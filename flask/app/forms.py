from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, PasswordField, FileField
from wtforms.validators import DataRequired, Email, Length, EqualTo, InputRequired 

class LoginForm(FlaskForm):
    email = StringField("Email: ", validators=[Email("Некорректный email")])
    psw = PasswordField("Пароль:", validators=[DataRequired(), Length(min=4, max=20, message = "Пароль должен содержать от 4 до 20 символов")])
    remember = BooleanField("Запомнить", default = False)
    submit = SubmitField("Войти")

class RegisterForm(FlaskForm):
    name = StringField("Имя:", validators=[DataRequired(), Length(min=0, max=20, message = "Введите имя длиной до 20 символов")])
    email = StringField("Email: ", validators=[Email("Некорректный email")])
    psw = PasswordField("Пароль:", validators=[DataRequired(), Length(min=4, max=20, message = "Пароль должен содержать от 4 до 20 символов")])
    psw2 = PasswordField("Повтор пароля:", validators=[DataRequired(), EqualTo("psw", message = "Пароли не совпадают")])
    submit = SubmitField("Зарегистрироваться")

class UploadFileForm(FlaskForm):
    file = FileField("File", validators=[DataRequired(message = "Выберите файл")])
    submit = SubmitField("Загрузить")