#------------------------MODULES--------------------------------------
from flask import abort,Flask, render_template, flash, redirect, url_for, request, session, logging
from flask_mysqldb import MySQL
from wtforms import Form,TextAreaField,StringField,PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
from time import sleep
#------------------------FORM CLASSES---------------------------------------
class RegisterForm(Form):
    name = StringField("İsminiz :",validators=[validators.Length(min=3, max=15,
    message="İsminiz 3-15 karakter uzunluğunda olmalıdır !")])

    username = StringField("Kullanıcı Adınız :",
    validators=[validators.Length(min=4, max=15,
    message="Kullanıcı adınız 4-15 karakter uzunluğunda olmalıdır !"),
    validators.DataRequired(message="Zorunlu alan")])

    email = StringField("E-mail :",
    validators=[validators.Email(message="Lütfen geçerli bir E-Mail giriniz !"),
    validators.DataRequired(message="Zorunlu alan")])

    password = PasswordField("Şifreniz :",
    validators=[validators.Length(min=8,max=20,message="Şifreniz 8-20 karakter uzunluğunda olmalı !"),
    validators.data_required(message="Şifre alanı boş bırakılamaz !"),
    validators.EqualTo(fieldname="passconfirm",
    message="Tekrar girilen şifre ile farklı bir şifre girdiniz !")])

    passconfirm = PasswordField("Şifrenizi Tekrar Girin :")

class LoginForm(Form):
    username = StringField("Kullanıcı Adı :")
    password = PasswordField("Şifre :")

class AddArticle(Form):
    title = StringField("Makale Başlığı :",
    validators=[validators.Length(min=5,max=35,message="Başlık 3-35 karakter arası olmalıdır.")])
    content = TextAreaField("Makale Konusu :",
    validators=[validators.Length(min=10,message="Makale en az 10 karakter içermelidir.")],
    render_kw={"rows":10})

#------------------------APP AND DB CONFIG---------------------------------------
app = Flask(__name__)
app.config["DEBUG"] = True
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "umut_blog"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)
app.secret_key = "umut_blog"

#------------------------DECORATORS---------------------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "login" in session:
                return f(*args, **kwargs)
        else:
            sleep(2)
            flash("Öncelikle giriş yapmanız gerek !","danger")
            return redirect(url_for("login"))
            
    return decorated_function

def logout_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "login" in session:
            return redirect("",304)
        else:
            return f(*args, **kwargs)
    return decorated_function

#------------------------REQUESTS---------------------------------------
#Main
@app.route("/")
def index():
    cur = mysql.connection.cursor()

    sorgu = "SELECT * FROM articles"
    result = cur.execute(sorgu)
    cur.close()
    return render_template("index.html",switch="on",result=result)

#About
@app.route("/about")
def about():
    cont=["Umut","Utku","Yasin","Çağatay"]
    return render_template("about.html",cont = cont)

#View Articles
@app.route("/article/<string:id>")
def article(id):
    cur = mysql.connection.cursor()
    sorgu = "SELECT * FROM articles WHERE id = %s"
    result = cur.execute(sorgu,(id,))

    if result > 0:
        article = cur.fetchone()
        cur.close()
        return render_template("viewarticle.html",article = article,id = id)
    else:
        return render_template("viewarticle.html")

#Articles
@app.route("/articles")
def articles():
    cur = mysql.connection.cursor()
    sorgu = "SELECT * FROM articles ORDER BY created_date DESC"
    result = cur.execute(sorgu)

    if result > 0:
        articles = cur.fetchall()
        cur.close()
        return render_template("articles.html",articles = articles)
    else:
        cur.close()
        return render_template("articles.html")

#Add Article
@app.route("/addarticle",methods=["GET","POST"])
@login_required
def addarticle():
    form = AddArticle(request.form)
    if request.method == "POST" and form.validate():
        try:
            title = form.title.data
            content = form.content.data

            cur = mysql.connection.cursor()
            sorgu = "INSERT INTO articles(title,author,content) VALUES(%s,%s,%s)"
            cur.execute(sorgu,(title,session["username"],content))
            mysql.connection.commit()
            cur.close()

            flash("Makaleniz başarıyla eklenmiştir !","success")
        except:
            flash("Makale başlığı veya içeriği zaten eklenmiş !","danger")

    return render_template("addarticle.html",form = form)

#Delete Article
@app.route("/delete/<string:id>",methods=["GET","POST"])
@login_required
def delete(id):
    #Get Request
    if request.method == "GET":
        cur = mysql.connection.cursor()
        sorgu = "SELECT * FROM articles WHERE id = %s AND author = %s"
        result = cur.execute(sorgu,(id,session["username"]))

        #Create 'delete.html' template
        if result > 0:
            article = cur.fetchone()
            cur.close()
            return render_template("delete.html",article = article)
        else:
            cur.close()
            return render_template("delete.html")

    #Post Request
    else:
        cur = mysql.connection.cursor()
        sorgu = "DELETE FROM articles WHERE id = %s and author = %s"
        result = cur.execute(sorgu,(id,session["username"]))
        mysql.connection.commit()
        cur.close()

        #Deleting Article
        if result > 0:
            flash("Makale başarıyla silindi.","success")
            return redirect("/dashboard")
        else:
            flash("Bir hata oluştu","danger")
            return redirect("/dashboard")

#Update Article
@app.route("/edit/<string:id>",methods=["GET","POST"])
@login_required
def update(id):
    #Get Request
    if request.method == "GET":
        cur = mysql.connection.cursor()
        sorgu = "SELECT * FROM articles WHERE id = %s AND author = %s"
        result = cur.execute(sorgu,(id,session["username"]))

        #Create 'update.html' template
        if result > 0:
            article = cur.fetchone()
            cur.close()
            form = AddArticle()
            form.title.data = article["title"]
            form.content.data = article["content"]
            return render_template("update.html",form = form)
        else:
            cur.close()
            return render_template("update.html")

    #Post Request
    else:
        form = AddArticle(request.form)
        newTitle = form.title.data
        newContent = form.content.data

        try:
            cur = mysql.connection.cursor()
            sorgu = "REPLACE INTO articles(id,title,author,content) VALUES(%s,%s,%s,%s)"
            cur.execute(sorgu,(id,newTitle,session["username"],newContent))
            mysql.connection.commit()
            cur.close()
        except:
            flash("Aynı başlık veya içerik zaten var.","danger")
            return redirect("/edit/"+id)

        flash("Makaleniz Güncellenmiştir","success")
        return redirect("/dashboard")

#Search Article
@app.route("/search",methods=["GET","POST"])
def search():
    #Get Request
    if request.method == "GET":
        return redirect("/articles")
    
    #Post Request
    else:
        keyword = request.form.get("keyword")
        cur = mysql.connection.cursor()
        sorgu = "SELECT * FROM articles WHERE title LIKE '%"+keyword+"%'"
        result = cur.execute(sorgu)

        if result > 0:
            articles = cur.fetchall()
            cur.close()
            return render_template("articles.html",articles = articles)
        else:
            cur.close()
            sleep(2)
            flash("Makale bulunamadı","danger")
            return redirect("/articles")

#Register
@app.route("/register",methods = ["GET","POST"])
@logout_required
def register():
    form = RegisterForm(request.form)
    name = form.name.data
    username = form.username.data
    email = form.email.data
    password = sha256_crypt.hash(form.password.data)

    if request.method == "POST" and form.validate():
        cur = mysql.connection.cursor()
        try:
            sorgu = "INSERT INTO users(name,email,username,password) VALUES(%s,%s,%s,%s)"
            cur.execute(sorgu,(name,email,username,password))
            mysql.connection.commit()
            cur.close()
            flash("Başarıyla kayıt oldunuz !","success")
            return redirect("/login")
        except:
            flash("Bu kullanıcı adı veya E-mail adresi zaten kayıtlı !","danger")
            cur.close()
            return redirect("/register")

    else:
        return render_template("register.html",form=form)

#Login    
@app.route("/login",methods=["GET","POST"])
@logout_required
def login():
    form = LoginForm(request.form)
    if request.method == "POST":
        username = form.username.data
        password = form.password.data

        cur = mysql.connection.cursor()
        sorgu = "SELECT * FROM users WHERE username = %s"
        db_request = cur.execute(sorgu,(username,))

        if db_request > 0 :
            data = cur.fetchone()
            encrypted_pass = data["password"]
            cur.close()

            if sha256_crypt.verify(password,encrypted_pass):
                flash("Başarıyla giriş yaptınız !","success")
                session["login"] = True
                session["username"] = username
                return redirect("/")
            else:
                sleep(2)
                flash("Şifrenizi yanlış girdiniz !","danger")
                return redirect("/login")

        else:
            sleep(2)
            flash("Böyle bir kullanıcı adı bulunamadı !","danger")
            cur.close()
            return redirect("/login")

    return render_template("login.html",form=form)

#Logout
@app.route("/logout")
@login_required
def logout():
    session.clear()
    flash("Başarıyla çıkış yaptınız !","success")
    return redirect("/")

#Dashboard
@app.route("/dashboard")
@login_required
def dashboard():
    cur = mysql.connection.cursor()
    sorgu = "SELECT * FROM articles WHERE author = %s ORDER BY created_date DESC"
    result = cur.execute(sorgu,(session["username"],))

    if result > 0:
        articles = cur.fetchall()
        cur.close()
        return render_template("dashboard.html",articles = articles)
    else:
        cur.close()
        return render_template("dashboard.html")

#To run the .py
if __name__ == "__main__":
    app.run()

