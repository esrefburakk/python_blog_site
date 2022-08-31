# -*- coding:utf-8 -*-
#AUTOINCREMENT olayı otomatik birer birer arttırma demektir.
import email
from email import message
from email.message import EmailMessage
from sre_constants import SUCCESS
from unicodedata import category
import MySQLdb
from click import password_option
from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps
#KAYIT FORMU
class Register_MyForm(Form):
    name = StringField('İsim Soyisim --> ',validators=[validators.Length(min=4,max = 25)])
    e_mail = StringField('Mail Adresiniz --> ',validators=[validators.Email(message="Geçersiz email adresi....")])
    username = StringField('Kullanıcı Adı -->',validators=[validators.data_required()])
    password = PasswordField('Şifreniz --> ',validators=[
        validators.DataRequired(message="Parola belirleyiniz..."),
        validators.EqualTo(fieldname = "re_password",message="Parolanız uyuşmuyor...")
    ])       
    re_password = PasswordField("Parola Doğrulama")
#LOGIN FORMU
class Login_MyForm(Form):
    username = StringField('Kullanıcı Adı -->')
    password = PasswordField('Şifre -->')
#MAKALE EKLEME FORMU
class addArticles(Form):
    title = StringField('Makalenizin Başlığı -->',validators=[validators.Length(min = 4,max = 50)])
    content = TextAreaField('Makalenizin İçeriği -->',validators=[validators.Length(min = 10)])
app = Flask(__name__)
app.secret_key = "ebtblog"
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "myblog"    
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

#bildiğimiz gibi decoreterler kendinden aşağıdaki fonksiyona kendi ile ilgili işlemleri aktarırlar ve tekrara düşürtmez.
#biz de route request olarak ayarlayıp yazacağımız fonksiyonun içine işlemlerini aktarıcaz. 

#ANA SAYFA KISMINA GİTME İÇİN
@app.route("/")
def index():
    return render_template("main_page_index.html")
"""
def index():
    inf = [
        
        {"id": 1, "name":"test1","content":"test1.content"},
        {"id": 2, "name":"test2","content":"test2.content"},
        {"id": 3, "name":"test3","content":"test3.content"}
        
    ]
    return render_template("index.html",inf = inf)
"""
#KULLANICI GİRİŞ DECORETERİ
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu sayfayı giriş yapmadan görüntülüyemezsiniz","danger")
            return redirect(url_for("login"))
    return decorated_function
#Aşağıda yaptığımız işlem aslında ana sayfamızın içine hakkında kısmı koymaktır. Bunu bu şekilde yazarak çoğaltabiliriz.
#HAKKIMDA
@app.route("/whoami")
def about():
    return render_template("about.html")
myblogsql = MySQL(app)
#MAKALE SAYFALARI(articles)
@app.route("/articles")
@login_required
def articles():
    cursor = myblogsql.connection.cursor()
    result = cursor.execute("SELECT * FROM makaleler")
    if result > 0:
        articles = cursor.fetchall()
        return render_template("makaleler.html",articles = articles)
    else:
        return render_template("makaleler.html")
#KAYIT OL
#form.validate methodu bize TRUE ya da FALSE değeri döndürür bu değerler içerisi dolu mu yani bilgi girildi mi işlemidir.
@app.route("/register",methods = ["GET","POST"])
def register():
    form1 = Register_MyForm(request.form)
    if request.method == 'POST' and form1.validate():
        name = request.form['name']
        email = request.form['e_mail']
        username = request.form['username']
        #sha256_crypt formatı database de şifrelerimizi şifrelemeye yarıyor.
        password = request.form['password']
        cursor = myblogsql.connection.cursor()
        cursor.execute("INSERT INTO users(name,email,username,password) VALUES(%s,%s,%s,%s)",(name,email,username,password))
        #aşağıda yazdığımız executenin içindeki demet yani (name,email,username,password) yukarıdaki valuesin içindeki %s ler yerine gelir.
        #veritabanındaki belirli bir güncelleme belirli bir değişiklik yapmak istediğimizde .commit() yazmamız gerekir.
        myblogsql.connection.commit()
        cursor.close()
        flash("Kayıt işlemi başarılı","success")
        return redirect(url_for("login"))
    else:
        return render_template("register.html",form = form1)
#LOGIN(GİRİŞ YAP)
#login_manager = LoginManager()
#login_manager.init_app(app)
@app.route("/login",methods = ["GET","POST"])
def login():
    form2 = Login_MyForm(request.form)
    if request.form:
        username = request.form['username']
        password = request.form['password']
        cursor = myblogsql.connection.cursor()
        result = cursor.execute("SELECT * FROM users WHERE username = %s",(username,))
        if result > 0:
            data = cursor.fetchone()
            real_password = data["password"]
            if real_password == password:
                flash("Başarıyla Giriş Yaptınız.","success")
                session["logged_in"] = True
                session["username"] = username
                return render_template("main_page_index.html")
            else:
                flash("Parolanızı Yanlış Girdiniz... Lütfen tekrar deneyiniz","danger")
                return redirect(url_for("login")) 
        else:
            flash("Böyle Bir Kullanıcı Adı Yoktur.","danger")
            return redirect(url_for("login"))   
    else:
        return render_template("login.html",form = form2)
#DETAY SAYFASI
@app.route("/articles/<string:id>")
@login_required
def detail(id):
    cursor = myblogsql.connection.cursor()
    result = cursor.execute("SELECT * FROM makaleler WHERE id = %s",(id,))
    if result > 0:
        article = cursor.fetchone()
        return render_template("detail_makale.html",article = article)
    else:
        return render_template("detail_makale.html")
#LOGOUT(ÇIKIŞ YAP)
@app.route("/logout")
@login_required
def logout():
    session.clear()
    flash("Başarıyla Çıkış Yaptınız.","danger")
    return render_template("main_page_index.html")
#DASHBOARD
#KULLANICI ADINA GÖRE MAKALELERİ GÖSTERME İŞLEMİNİ YAPTIK
@app.route("/kontrol_paneli")
@login_required
def kontrol_paneli():
    cursor = myblogsql.connection.cursor()
    result = cursor.execute("SELECT * FROM makaleler WHERE author = %s",(session["username"],))
    if result > 0:
        articles = cursor.fetchall()
        return render_template('kontrol_paneli.html', articles=articles)
    else:
        return render_template("kontrol_paneli.html")
#MAKALE EKLE
@app.route("/makale_ekle",methods=["GET", "POST"])
@login_required
def makale_ekle():
    form3 = addArticles(request.form)
    if request.method == "POST" and form3.validate():
        title = request.form['title']
        content = request.form['content']
        cursor = myblogsql.connection.cursor()
        cursor.execute("INSERT INTO makaleler(title,author,content) VALUES(%s,%s,%s)",(title,session["username"],content))
        myblogsql.connection.commit()
        cursor.close()
        flash("Makale Ekleme İşleminiz Başarılı","success")
        return render_template("kontrol_paneli.html")
    else:
        return render_template("makale_ekle.html",form = form3)
#MAKALE_SİL
@app.route("/sil/<string:id>")
@login_required
def makale_sil(id):
    cursor = myblogsql.connection.cursor()
    result = cursor.execute("SELECT * FROM makaleler WHERE author = %s and id = %s",(session["username"],id)) 
    if result > 0:
        cursor.execute("DELETE FROM makaleler WHERE id = %s",(id,)) 
        myblogsql.connection.commit()
        return redirect(url_for("kontrol_paneli"))
    else:
        flash("BÖYLE BİR MAKALE YOKTUR VEYA BÖYLE BİR MAKALEYİ SİLMEDE YETKİNİZ BULUNMAMAKTADIR.","danger")
        return render_template("main_page_index.html")
#MAKALE_GÜNCELLE
@app.route("/düzenle/<string:id>",methods=["GET", "POST"])
@login_required
def edit(id):
    if request.method == "GET":
        cursor = myblogsql.connection.cursor()
        result = cursor.execute("SELECT * FROM makaleler WHERE id = %s and author = %s",(id,session["username"]))
        if result == 0:
            flash("Böyle bir makale yok veya bu işleme yetkili değilsiniz.","danger")
            return render_template("main_page_index.html")
        else:
            article = cursor.fetchone()
            form = addArticles()
            form.title.data = article["title"]
            form.content.data = article["content"]
            return render_template("update_makale.html",form = form)
    else:
        #POST REQUEST KISMI
        form = addArticles(request.form)
        newTitle = form.title.data
        newContent = form.content.data
        
        cursor = myblogsql.connection.cursor()
        cursor.execute("UPDATE makaleler SET title = %s,content = %s WHERE id = %s",(newTitle,newContent,id))
        myblogsql.connection.commit()
        
        flash("Makale başarıyla güncellendi...","success")
        return redirect(url_for("kontrol_paneli"))
#MAKALE ARA
@app.route("/search",methods=["GET", "POST"])
def makale_ara():
    if request.method == "GET":
        return render_template("main_page_index.html")
    else:
        keyword = request.form.get("keyword")
        cursor = myblogsql.connection.cursor()
        result = cursor.execute("SELECT * FROM makaleler WHERE title LIKE '%" + keyword + "%'")
        if result == 0:
            flash("Aradığınız makale bulunmamaktadır.")
            return render_template("makaleler.html")
        else:
            articles = cursor.fetchall()
            return render_template("makaleler.html",articles = articles)
#Aşağıda yaptığımız işlem dinamik url yapısı oluşturmamızı sağlar.
"""
@app.route("/article/<string:id>")
def detail(id):
    return "Article ID:" + id
"""    
if __name__ == "__main__":
    app.run(debug=True)