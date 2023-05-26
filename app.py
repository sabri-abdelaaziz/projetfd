#import of libriries

from mysql.connector import connect
from datetime import date 
import os 
import json
import datetime
import random
from flask import Flask, render_template, request , redirect , url_for , session,jsonify
import matplotlib.pyplot as plt 
import numpy as np 
import plotly.express as px 
import plotly
import plotly.graph_objs as go 
import pandas as pd 
import io 
import base64 
import tensorflow as tf 
from matplotlib.backends.backend_agg  import FigureCanvasAgg as FigureCanvas 
import secrets  
from PIL import Image 
import numpy as np 
from PIL import ImageOps 
from tensorflow.keras.models import load_model 
from flask_mail import Mail, Message




# cclass for date Json 

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.date):
            return obj.isoformat()
        return super().default(obj)




# initialisation the application

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)



#buyProductStripe contains the cart product
buyProductStripe = []

#stripe getway
@app.route('/create-checkout-session',methods=["POST"])
def create_checkout_session():

    if request.method == "POST" :
        send_email = request.form["send_email"]
        send_phone = request.form["send_phone"]
        send_street = request.form["send_street"]
        send_city = request.form["send_city"]

    
    line_items = []
        
        
    for result in buyProductStripe[0]:
        line_items.append({
                "price": result[-1],
                "quantity": result[4]
            })
        # redirect to the checkout session with the line items
        checkout_session = stripe.checkout.Session.create(
                line_items=line_items,
                mode="subscription",
                success_url=YOUR_DOMAIN + f"/success?email={send_email}&phone={send_phone}&street={send_street}&city={send_city}",
                cancel_url=YOUR_DOMAIN + "/cancel.html"
            )
        
        
    return redirect(checkout_session.url,code=303)


# if the visa processus is success
@app.route("/success")
def success():

    send_email = request.args.get('email')
    send_phone = request.args.get('phone')
    send_street = request.args.get('street')
    send_city = request.args.get('city')
    id_client = session["id"]
    paiment = "Visa"
    conn = connection()

    #return "cart" if any input is empty

    if not(send_email or send_phone or send_street or send_city):
        return redirect("/cart")

    #add demmande from success visa 
  
    sql = "SELECT * FROM cart c , product p where c.id_product = p.id and c.id_client = %s"
    cursor.execute(sql, (id_client,))
    result = cursor.fetchall()
    for t in result :
        values = (id_client, t[2]  , date.today() , t[4] , send_city , send_street , send_phone , paiment)
        cursor.execute("INSERT INTO demande(id_client,id_product,dateDemande , quantity , city, adresse , tel ,paiment_tool ) values(%s , %s , %s , %s , %s,%s,%s,%s)",values)
        conn.commit()
    cursor.close()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cart WHERE id_client = %s" , (id_client,))
    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for("cart"))


#count the cart products

def cart_count() :
    if "email" in session:
        idu=session["id"]
        conn = connection()
        cursor = conn.cursor()
        sql = "SELECT count(id) FROM cart where id_client=%s"
        cursor.execute(sql,(idu,))
        results = cursor.fetchall()
        session["cart"]=results[0][0]

# apply to all pages
@app.before_request
def before_request():
    if request.path != '/verify_code' and  request.path != '/reset_password'  and  request.path != '/change_password' and  request.path != '/login':
        cart_count()
   
    



#connection of database
def connection():

    conn = connect(
        
        host="localhost",
        user="root",
        password="",
        database="fashionDb")

    return conn




# envoyez les stars  de produits

@app.route("/send_stars" , methods = [ "POST" , "GET" ])
def send_stars():
    if request.method == "POST":
        produitStars = request.form["produitStars"]
        produitId = request.form["produitId"]
        conn = connection()
        cursor = conn.cursor()
        sql = "Update   product SET stars = %s  where id=%s"
        values = (produitStars , produitId)
        cursor.execute(sql, values)
        conn.commit()
        cursor.close()
        conn.close()
        rv=produitId
        session[rv] = "True"
        return redirect(f"/product?id={produitId}")
    return redirect(url_for("shop"))   




# add user's satisfaction
@app.route("/satesfaction_clients" , methods = [ "POST" , "GET" ])
def satisfaction():
    if request.method == "POST":
        stars = request.form["nbr_stars"]
        idclient = session["id"]
        stars=int(stars)
        conn = connection()
        cursor = conn.cursor()
        sql = "insert into satisfaction(id_user,stars) values( %s , %s)"
        values = (idclient , stars)
        cursor.execute(sql, values)
        conn.commit()
        cursor.close()
        conn.close()
        session["err_cart"]="Thanks for your openion , we will try to improve your shopping"

   
        return redirect("/cart")
    return redirect(url_for("login"))   




@app.route("/reset_password" , methods = ["POST" , "GET"])
def send():

    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 465
    app.config['MAIL_USE_SSL'] = True
    app.config['MAIL_USERNAME'] = 'azizsabri072@gmail.com'
    app.config['MAIL_PASSWORD'] = 'easackxscqstxzit'

 
    if request.method == "POST" :

        email = request.form["email"]

        code = str(secrets.randbelow(10**3)).zfill(3)
        session["code"] = code
        session["email"] = email
        

        mail = Mail(app)
        mail_message = Message(
        code, 
        sender =   'azizsabri072@gmail.com', 
        recipients = [str(email)])
        mail_message.body = "This is the code of verfication to reset your password"
        mail.send(mail_message)
        return render_template("reset_password.html")

    else :
        return render_template("reset_password.html")
          


@app.route('/verify_code',methods=["GET","POST"])
def verify_code():
    if request.method =="POST":
        code=request.form["code"]
        real_code=session["code"]
        if code!=real_code:
            return render_template("reset_password.html")
        else:
             return render_template("reset_password.html",code_verify=True)
    

    return redirect(url_for("login"))


@app.route('/change_password',methods=["GET","POST"])
def change_password():
    if request.method =="POST":
        password=request.form["password"]
        rpassword=request.form["rpassword"]
        email=session["email"]
       
        if password!=rpassword:
            return render_template("reset_password.html",code_verify=True)
        else:
            conn=connection()
            cursor = conn.cursor()
            sql = "Update   users SET password=%s where email=%s"
            values = (password,email) 
            cursor.execute(sql, values)
            conn.commit()
            cursor.close()
            conn.close()
            return redirect(url_for("login"))
            
    

    return redirect(url_for("login"))





#index pages 

#(select messages and these image of profil)
#(select 4 profuct with shaffle)



@app.route('/')
def index():
    

    session.pop("err",None)
    conn = connection()
    cursor = conn.cursor()
    sql = "SELECT * FROM message m,users u where u.email=m.email"
    cursor.execute(sql)
    results = cursor.fetchall()

    cursor1 = conn.cursor()
    sql1 = "SELECT * FROM product"
    cursor1.execute(sql1)
    resulta = cursor1.fetchall()
    random.shuffle(resulta) 
    res=resulta[:4]


  

   



   
    return render_template("home.html",messages=results,feauture_product=res) 

# add numer of likes to the message  

@app.route("/message/adore",methods=["GET","POST"])
def adore():
    conn = connection()
    cursor = conn.cursor()
    id = request.args["id"] 
    sql1 = "SELECT * FROM message where id=%s "
    cursor.execute(sql1,(id,))
    r= cursor.fetchall()

    #get the number of likes 
    adore=r[0][5]

    cursor = conn.cursor()

    #change it 
    sql = "Update   message SET adore=%s where id=%s"
    values = (adore+1,id )
    cursor.execute(sql, values)
    conn.commit()
    cursor.close()
    conn.close()


    #return a lapae index on the id messages 
    return redirect("/#footer")




# about page to go the page about

@app.route('/about')
def about():
    
    
    return render_template('about.html')
  

  #shop pages toshow all product that we have 
  #if we have some search from the user after upload image to search

@app.route('/shop')
def shop():
    

    if "classe" in session: 
        classe=session["classe"]
    conn = connection()
    
    #if wedon't have the search
    if not "classe" in session:
        cursor = conn.cursor()
        sql = "SELECT * FROM product order by stars  desc "
        cursor.execute(sql)
        results = cursor.fetchall()
    
        return render_template('shop.html' , data=results)


    cursor = conn.cursor()
    sql = "SELECT * FROM product"
    cursor.execute(sql)
    results = cursor.fetchall()
    cursor.close()
    cursor = conn.cursor()

   #we select the productwith the some type of the user search
    if "classe" in session:
        sql = "SELECT * FROM product where label=%s"
        cursor.execute(sql,(classe,))
        resultsClasses = cursor.fetchall()
        cursor.close()

        session.pop("classe", None)
        return render_template('shop.html' , data=results,resultsClasses=resultsClasses)
    
    return render_template('shop.html' , data=results)
    
    




#page to show information about the product
#and also. show 5 ofthe smae product

@app.route('/product', methods = ['POST' , 'GET'])
def product():
    

    
    product_id = request.args.get('id')
    
    conn = connection()
    cursor = conn.cursor()
    sql = "SELECT * FROM product where id = %s"
    sqlForChoose = "SELECT * FROM product where label = %s"

    cursor.execute(sql , (product_id,))
    results = cursor.fetchall()        


    cursor.execute(sqlForChoose , (results[0][1],))
    resultsForChooseImage = cursor.fetchall()  
    random.shuffle(resultsForChooseImage) 
    chooseIm =  resultsForChooseImage[:4]
    random.shuffle(resultsForChooseImage) 
 
    
    return render_template('product.html' , data =results , ci = chooseIm,feautures=resultsForChooseImage)
    
#the cart is when we shou the products of users 
#after selectin the id i n login

@app.route('/cart' , methods=['GET' , 'POST'])
def cart():
    

    #requirement of doing login
    if 'email' in session and 'password' in session :
        email = session['email']
        tel = session['tel']
        
        
        
        conn = connection()
        
        #if the requist is post to add product to cart
        if request.method == "POST":
            quantity = request.form["quantity"]
            id_product = request.form["id_product"]
            id_client = session['id']
            dateToday = date.today()
        
            
            cursor = conn.cursor()
            sql = "INSERT INTO cart(id_client , id_product ,dateAdd,quantity  ) values(%s , %s , %s , %s )"
            cursor.execute(sql , (id_client , id_product , dateToday , quantity ))
            conn.commit()
            conn.close()
            #add product and show the cart
            session["err_cart"]="you  add the product successfully "
            return redirect(url_for("cart"))
        
        #joint the product and the cart by id product
        cursor = conn.cursor()
        sql = "SELECT * FROM cart c , product p where c.id_product = p.id and c.id_client = %s"
        id_client = session['id']
        cursor.execute(sql , (id_client,))
        results = cursor.fetchall()
        #calculate of anyproduct the price *quantity in cart
        total = "SELECT sum(p.price * c.quantity) FROM cart c , product p where c.id_product = p.id and c.id_client = %s "
        cursor.execute(total , (id_client,))
        sumTotal = cursor.fetchall()

        buyProductStripe.append(results)
        
        return render_template("cart.html", buyProduct = results , total = sumTotal , email = email , tel = tel)
    
    #if the user doesn'texist in the session
    return redirect(url_for("shop"))



   
   
   
# for admin to see. details of demmandes 
@app.route('/admin/demmands')
def demandes():

    conn = connection()
    cursor = conn.cursor()
    sql = "SELECT * FROM demande d, users u , product p where d.id_client = u.id and d.id_product = p.id"
    cursor.execute(sql)
    results = cursor.fetchall()

    conn1 = connection()
    cursor = conn1.cursor()
    sql1 = "SELECT dateDemande ,sum(quantity) FROM demande group by dateDemande "
    cursor.execute(sql1)
    data = cursor.fetchall()
    dates = []
    quantity = []
    for i in data :
        dates.append(i[0])
        quantity.append(str(i[1]))
    

    conn2 = connection()
    cursor = conn2.cursor()
    sql2 = "SELECT count(id_user),stars FROM satisfaction group by stars "
    cursor.execute(sql2)
    resultSatisfaction = cursor.fetchall()

    d = {}
    for i in resultSatisfaction :
        if i[1] not in d :
            d[i[1]] = i[0]
        
    resultSatisfaction = d



    







        
    lien="demmandes"

    # Convert `results` to JSON string using custom encoder
    DD = np.array(results)
    DD = DD[:, 3]
    DD = pd.DataFrame(DD, columns=["Dates Demands"])
    DD = DD["Dates Demands"].value_counts().to_dict()

    # Convert keys to strings
    DD = {str(k): v for k, v in DD.items()}
    for k in DD:
        DD[k] = str(DD[k])
    DDQ = np.array(results)
    DDQ = DDQ[: , 3:5 ]
    DDQ = pd.DataFrame(DDQ , columns=["Dates Demands" , "quantity"])
    DDQ['quantity'] = pd.to_numeric(DDQ['quantity'])
    DDQ = DDQ.groupby("Dates Demands")["quantity"].sum().to_dict()
    DDQ = {str(k): str(v) for k, v in DDQ.items()}
    return render_template('admin_manage/admin_dashboard.html',data=results,lien=lien , DD=DD , DDQ = DDQ   ,resultSatisfaction=resultSatisfaction)


#suivre demandes
@app.route("/suivre_demande")
def suivre_demade():
    

    id_client=session["id"]
    conn = connection()
    cursor = conn.cursor()


    sql = "SELECT  quantity,city,adresse,tel,valider from demande where id_client =%s"
    cursor.execute(sql,(id_client,))
    results = cursor.fetchall()
   
       
    return render_template("suivre_demande.html",data=results)




#for admin to see all users
#see all the information about clients
@app.route('/clients')
def client():
    

    conn = connection()
    cursor = conn.cursor()
    sql = "SELECT * FROM users"
    cursor.execute(sql)
    results = cursor.fetchall()
    lien="clients"
    DC = np.array(results)
    DC = DC[: ,  5]
    DC = pd.DataFrame(DC , columns=["address"]) 
    DC = DC["address"].value_counts().to_dict()
    for e in DC:
        DC[e] = str(DC[e])
    return render_template('admin_manage/admin_dashboard.html',data=results,lien=lien , DC = DC)



#show_date

@app.route("/date_show",methods = ["POST", "GET"])
def showdate():

    if request.method == "POST":
        date_selected = request.form["date"]
        conn = connection()
        cursor = conn.cursor()
        sql = "SELECT  quantity,city,adresse,tel,valider from demande WHERE dateDemande = %s"
        cursor.execute(sql , (date_selected,))
        results = cursor.fetchall()
 
        cursor = conn.cursor()
        sql = "SELECT count(city) from demande where dateDemande = %s"
        cursor.execute(sql , (date_selected,))
        results1 = cursor.fetchall()

        num_demands=results1
        return render_template("livreur.html" , data = results , date_selected = date_selected,num_demands=num_demands )
    return redirect(url_for("livreur"))




@app.route('/livreur')
def livreur():
    
    if not "livreur" in session:
        return redirect(url_for("login"))

    date_selected = date.today()
    conn = connection()
    cursor = conn.cursor()
    sql = "SELECT  id,quantity,city,adresse,tel,valider from demande WHERE dateDemande = %s"
    cursor.execute(sql , (date_selected,))
    results = cursor.fetchall()

    cursor = conn.cursor()
    sql = "SELECT count(city) from demande where dateDemande = %s"
    cursor.execute(sql , (date_selected,))
    results1 = cursor.fetchall()

    num_demands=results1
    return render_template("livreur.html" , data = results , date_selected = date_selected,num_demands=num_demands )
    

# here is the dashboard of the adin to manage all setting

@app.route('/update_role',methods=["POST","GET"])
def update_role():
   

    if request.method=="POST":
        role=request.form["update_role"]
        id=request.form["id-client"]
    

        conn = connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET role=%s WHERE id=%s', (role,id))
        conn.commit()
        conn.close()
        return redirect(url_for("client"))



    return redirect(url_for("login"))




@app.route('/admin')
def admin():
    

    if "id" in session and session["email"]=="admin@gmail.com":
        
        conn = connection()
        cursor = conn.cursor()
        sql = "select sum(d.quantity*p.price)  from product p , demande d where d.id_product = p.id  and d.dateDemande = %s "
        cursor.execute(sql , (date.today(),))
        result = cursor.fetchall()
        
        
        sql1 = "select sum(price)  from product"
        cursor.execute(sql1 )
        result2 = cursor.fetchall()

        sql3 = "select count(id)  from users"
        cursor.execute(sql3 )
        result3 = cursor.fetchall()
        sp = "select p.label , sum(d.quantity*p.price)  from product p , demande d where d.id_product = p.id  group by p.label "
        
        cursor.execute(sp)
        someOfsp = cursor.fetchall()
        
        arr = np.array(someOfsp)
        
        products = "select count(label) , label , stars from product group by label , stars"
        cursor.execute(products)
        resultProduct = cursor.fetchall()
        resultProduct = np.array(resultProduct)
        d = {}
        for i in resultProduct :
            if i[1] in d :
                d[i[1]].append([str(i[2]) , str(i[0]) ])
            elif i[1] not in d :
                d[i[1]] = [[str(i[2]) ,str(i[0])] ]
        resultProduct = d
 

       # resultProduct = [( var[0] , str(var[1]     ) ) for var in resultProduct]

        from itertools import groupby
       # resultProduct  = { t[1]:[] for t in resultProduct  }
        

        #resultProduct  =resultProduct[t[1]].append([t[0], t[2]]) for t in resultProduct])
  

       


        Label = []
        Stars = []
        for e in resultProduct :
            Label.append(e[0])
            Stars.append(e[1])
            
       # resultProduct = {'Labels':Label,'Stars':Stars}

        cursor.close()
        conn.close()
                        
        lien="section1"
       
        X = []
        Y = []
        for e in someOfsp :
            X.append(e[0])
            Y.append(str(e[1]))
        
        plot_data = {'x':X,'y':Y}

        
    
        
        return render_template('admin_manage/admin_dashboard.html' , plot=plot_data, fq = result , sq = result2 , tq = result3, resultProduct = resultProduct  )
    return redirect("/login")



  




#add new products to the database
#see the etails of all products in the same page
@app.route("/admin/products", methods=["GET", "POST"])
def admin_products():
    conn =connection()
    if request.method == "POST":
        titre = request.form["titre"]
        description = request.form["description"]
        prix = request.form["prix"]
        image = request.files['image']
      
       
        image_filename = image.filename
        image.save('static/images/uploads/' + image_filename)

        DP = {}
        
        if( not titre or not description or not image_filename or not prix ):
            session["err"]="someting went wrong"
            return  redirect("/admin/products" , DP = DP )
        else:
            cursor = conn.cursor()
            sql = "INSERT INTO product (label,designation,price, image) VALUES (%s, %s,%s, %s)"
            values = (titre, description,prix, image_filename)
            cursor.execute(sql, values)
            conn.commit()
            cursor.close()
            conn.close()
            return redirect("/admin/products" , DP = DP )
    else:

        #afficher les produits

        conn = connection()
        cursor = conn.cursor()
        sql = "SELECT * FROM product"
        cursor.execute(sql)
        results = cursor.fetchall()
        lien="products"
        DP = np.array(results) 
        DP = pd.DataFrame(DP[: , 1] , columns=["label"]) 
        DP = DP["label"].value_counts()
        DP = dict(DP)
        for e in DP :
            DP[e] = str(DP[e])
        DP = DP 
        return render_template('admin_manage/admin_dashboard.html',data=results,lien=lien ,  DP = DP)
   


        
       



#registre



@app.route("/registre", methods=["GET", "POST"])
def registre():
    

    session.pop("err",None)
    if request.method == "POST":
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        email = request.form["email"]
        addresse = request.form["addresse"]
        password = request.form["password"]
        rpassword = request.form["rpassword"]
        telephone = request.form["telephone"]

        image = request.files['image']
      
       # add profil image not required
       
        image_filename = image.filename
        if image_filename !="":
            image.save('static/images/uploads/profils/' + image_filename)
        else:
            image_filename="noprofil.png"

        

        if( not first_name or not last_name or not email or not addresse or not password or not rpassword or not telephone  ):
            session["err_registre"]="sorry some informations were  incorrect ! plaise try again"

            return render_template("registre.html")
        elif(rpassword!=password):   
            session["err_registre"]="sorry some informations were  incorrect ! plaise try again"

            return render_template("registre.html")
       
        else:
            conn = connection()

            cursor = conn.cursor()
            
            sql = "INSERT INTO users (first_name,last_name,password, email,addresse,telephone,image) VALUES (%s, %s,%s, %s,%s, %s,%s)"
            values = (first_name, last_name,password, email,addresse, telephone,image_filename)
            cursor.execute(sql, values)
            conn.commit()
            cursor.close()
            conn.close()
            session["err_login"]="you have add your account with success"

            return render_template("login.html")
    else:
        return render_template("registre.html")
       




#delete the user in the admin/client manage with id 

@app.route('/delete_user/<int:id>', methods=['post',"get"])
def delete_user(id):
    if "id" in session and session["email"]=="admin@gmail.com":
        id=int(id)
        # Delete the user
        conn = connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM users WHERE id=%s', (id,))
        conn.commit()
        conn.close()
        return redirect("/clients")
    return redirect("/login")
    






#allow admin to delee the product in the database 

@app.route('/delete_product/<int:id>', methods=['post',"get"])
def delete_product(id):

    if "email" in session and session["email"]=="admin@gmail.com":
        id=int(id)
        # Delete the user
        conn = connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM product WHERE id=%s', (id,))
        conn.commit()
        conn.close()
        return redirect(url_for("admin_products"))
    return redirect("/login")
    



# admin delete message with id of the message
@app.route('/delete_message/<int:id>', methods=['post',"get"])
def delete_message(id):
    if "email"  in session and  session["email"]=="admin@gmail.com":
        id=int(id)
        # Delete the user
        conn = connection()

        cursor = conn.cursor()
        cursor.execute('DELETE FROM message WHERE id=%s', (id,))
        conn.commit()
        conn.close()
        return redirect("/admin/messages")
    return redirect("/login")




# admin delete demande from the databasewith the id in get requist
@app.route('/delete_demande/<int:id>', methods=['post',"get"])
def delete_demande(id):
    if "id" in session and session["email"]=="admin@gmail.com":
        id=int(id)
        # Delete the user
        conn = connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM demande WHERE id=%s', (id,))
        conn.commit()
        conn.close()
        return redirect(url_for("demandes"))
    return redirect("/login")


# admin valider message to show it in the home page

@app.route('/valider_message/<int:id>/<valider>', methods=['post',"get"])
def valider_message(id,valider):
    if "id" in session and session["email"]=="admin@gmail.com":
        id=int(id)
        valider=valider
        # Delete the user
        conn = connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE message SET valider=%s WHERE id=%s', (valider,id))
        conn.commit()
        conn.close()
        return redirect(url_for("ges_message"))
    return redirect("/login")


#valider le de cients pr l'admin c'est il etait suiver 

@app.route('/valider_demande/<int:id>/<valider>', methods=['post',"get"])
def valider_demande(id,valider):
    id=int(id)
    valider=valider
    print(id)
    print(valider)
    # Delete the user
    conn = connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE demande SET valider = %s WHERE id = %s', (valider,id))
    conn.commit()
    conn.close()
    return redirect("/livreur")



#contact to allow users to let us some messages
@app.route('/contact',methods=["POST","GET"])
def contact():
    session.pop('err', None)
    conn =connection()
    if request.method == "POST":
        message = request.form["message"]
        email = request.form["email"]
        name = request.form["name"]
        date_creation= date.today()
        if( not message or not email or not name  ):
            session["err"]="you form are empty please complite all field"
            return  redirect("/contact")
        else:
            cursor = conn.cursor()
            sql = "INSERT INTO message (message,date_creation,name, email) VALUES (%s, %s,%s, %s)"
            values = (message, date_creation,name, email)
            cursor.execute(sql, values)
            conn.commit()
            cursor.close()
            conn.close()
            session["err"]="Thanks for your message !"

            
    
    return render_template("contact.html")




#gestion des messages allow admin to organize the messaes 
@app.route('/admin/messages')
def ges_message():
    if "id" in session and session["email"]=="admin@gmail.com":
        conn = connection()
        cursor = conn.cursor()
        sql = "SELECT * FROM message"
        cursor.execute(sql)
        results = cursor.fetchall()
        lien="messages"
        return render_template('admin_manage/admin_dashboard.html',data=results,lien=lien)
    return redirect("/")
   

    

#verification of user existance
#if the user is actualyin database


@app.route("/existe/user" , methods=['GET', 'POST'])
def exist():
    conn = connection()
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        if email =="" or password=="":
            session["err_login"]="username or password are empty"
        cursor = conn.cursor()
        query = "SELECT * FROM users WHERE email = %s and password = %s "
        # Execute the query with the parameter
        cursor.execute(query, (email, password))
        result = cursor.fetchall()
        cursor.close()
        conn.close()
        if len(result) == 0 :
            session["err_login"]="username or password incorrect"
            return redirect(url_for("login"))
        session["email"] = email
        session["password"] = password
        session["id"]=result[0][0]
        session["name"]=result[0][1]
        session["image"]=result[0][8]
        session["tel"] = result[0][6]
        if result[0][-2] == "livreur":
            session["livreur"]=True
            return redirect(url_for("livreur"))
        session["err_shop"]="Welcome,  {}".format(result[0][1])
        if(email=="admin@gmail.com" and password=="admin"):
            session["err_index"]="welcome admin"
            return redirect(url_for("admin"))
        return redirect(url_for("shop" ))



 #login
@app.route('/login' )
def login():
    return render_template("login.html"  )


 #logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")



 # Delete the products in cart
 #allow user to delete the prouct i the cart
@app.route("/delete/product/cart/<int:id>" , methods=["POST" , "GET"])
def deleteProduct(id):
    if "id" in session:
        id=int(id)
        conn = connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM cart WHERE id=%s', (id,))
        conn.commit()
        conn.close()
        session["err_cart"]="the product was deleted "
        return redirect("/cart")
    
    return redirect("/login")



#add demandes allow user to add the demmande
# delete all products in cart  and add it to the demand of admin

@app.route("/add/demande", methods=["GET", "POST"])
def addDemande():
    conn=connection()
    if request.method == "POST":
        email = request.form["email"]
        tel = request.form["tel"]
        street = request.form["street"]
        city = request.form["city"]
        id_client = session['id']
        paiment=request.form["paiment"]
        total=request.form["somme"]
        total=float(total)
        session["total"]=total
        if email==""  or tel=="" or street=="" or city=="":
            session["err_cart"]="somme data are empty"
            return redirect("/cart")
        cursor = conn.cursor()
        if( not email or not tel or not street or not city or not id_client):
            return redirect(url_for("cart"))
        sql = "SELECT * FROM cart c , product p where c.id_product = p.id and c.id_client = %s"
        cursor.execute(sql, (id_client,))
        result = cursor.fetchall()
        for t in result :
            values = (id_client, t[2]  , date.today() , t[4] , city ,street, tel,paiment)
            cursor.execute("INSERT INTO demande(id_client,id_product,dateDemande , quantity , city, adresse , tel ,paiment_tool ) values(%s , %s , %s , %s , %s,%s,%s,%s)",values)
            conn.commit()
        cursor.close()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cart WHERE id_client = %s" , (id_client,))
        conn.commit()
        cursor.close()
        conn.close()
        if paiment=="Paypal":
            session["total"]=(total*8)/100
            return render_template("paiment.html",paiment="Paypal")

        if paiment=="Visa":
            return render_template("paiment.html",paiment="Visa")


        return redirect(url_for("shop"))
    return redirect(url_for("cart"))
     
    

#the predictsesionhere we appload the training model and the image
#and receive the image

model = load_model('templates/fashionmodel.h5')


# Define the classes for the predictions
classes = np.array([
    'Shirt', 'Trouser', 'Pullover', 'Dress', 'Coat',
    'Sandal', 'Shirt', 'sneakers', 'Bag', 'ankle bots'
])



@app.route('/predict', methods=['POST'])
def predict():
    # Load the image
    image2 = request.files['image']
    image_filename = image2.filename
    image2.save('static/images/'+image_filename)
    image2 = Image.open('static/images/'+image_filename)
    image2 = image2.convert('L')
    image2 = image2.resize((28, 28))
    image2 = ImageOps.invert(image2)
    image_array =  np.array(image2 , dtype = 'float32')
    image_array = image_array.flatten()
    image_array = image_array.reshape((28, 28))
    image_array/=255
    image = image_array.reshape( 1 ,28, 28, 1)
    # donner l'image a notre model to predict it and give us the argmax for us it's the index of classes 
    prediction = model.predict(image).argmax()
    res=classes[prediction]
    #add the name to session to search
    session["classe"]=res
    print(res)
    return redirect("/shop")



#paiment tools
import paypalrestsdk
paypalrestsdk.configure({
  "mode": "sandbox", # 
  "client_id": "AV5VTPwXa2aJwMAG3tR9sacZuOeQf5-PxgXN7XFzq0ojmfpKrzLB0OZyOZBzvdkUjlB43x3W2y1dRmf5",
  "client_secret": "EC1C3074a8mVjsEPdAj0yhAV-5rpEzwJIHX0I8RQxTt1cQ2NjKjlDTWN2Sp0Hzxltd5lIvpPv2mXt5rg" })
  
@app.route('/payment', methods=['POST'])
def create_payment():
    # Replace with your own payment creation code
    #convert DH to Dollar
    payment = paypalrestsdk.Payment({
        'intent': 'sale',
        'payer': {
            'payment_method': 'paypal'
        },
        'transactions': [{
            'amount': {
                'total': str(session["total"]),
                'currency': 'USD'
            }
        }],
        'redirect_urls': {
            'return_url': 'http://localhost:5000/execute',
            'cancel_url': 'http://localhost:5000/'
        }
    })
    if payment.create():
        return jsonify({'paymentID': payment.id})
    else:
        return jsonify({'error': payment.error})

# execute paimeint
@app.route('/execute', methods=['GET'])
def execute_payment():
    payment_id = request.args.get('paymentId')
    payer_id = request.args.get('PayerID')
    if payment_id is None or payer_id is None:
        return jsonify({'error': 'Payment ID and Payer ID are required.'})
    payment = paypalrestsdk.Payment.find(payment_id)
    if payment.execute({'payer_id': payer_id}):
        return jsonify({'success': True})
    else:
        return jsonify({'error': payment.error})

    
#paypalt tool
@app.route("/pay_paypal" ,methods=["POST","GET"])
def pay():
    if "email" in session:
        return render_template("paiment.html")
    return redirect("login")


import stripe
stripe.api_key = "sk_test_51MsSotHTPZ6zTxVrkz4yBNhCEaDZGqylVWSYF7jvBnbEfrQXC3Pz6rkXJJZWyKcEjDxnhDEj58D6EeBk04v0rfv900FSFmqaRW"
YOUR_DOMAIN = "http://localhost:5000"

stripeProducts = []

@app.route("/sendProductToStripe")
def sendProductTostripe():
    conn = connection()
    cursor1 = conn.cursor()
    sql1 = "SELECT * FROM product"
    cursor1.execute(sql1)
    result = cursor1.fetchall()
    i=0
    cursorStripe = conn.cursor()
    for p in result:
        product = stripe.Product.create(
        name=p[1]+str(i),
        description=p[2],
        images=[f"static/images/clothes/all/{p[-3]}"]
    )
        i+=1
        price = stripe.Price.create(
            unit_amount=int(p[-4]),
            currency="usd",
            product=product.id,
            recurring={
                "interval": "month",
                "interval_count": 1,
                "usage_type": "licensed",
            }
        )
        
        sqlStripe = "Update  product SET price_id = %s where id = %s "
        cursorStripe.execute(sqlStripe, (price.id , p[0] ))
        conn.commit()
    conn.close()
    return stripeProducts

@app.route("/delet_all_stripe_products")
def delete_all_products():
    
    products = stripe.Product.list()
    for product in products:
        product_id = product.id
        # Get all the prices associated with the product
        prices = stripe.Price.list(product=product_id).data

        # Delete all the prices associated with the product
        for price in prices:
            stripe.Price.modify(
            price.id,
            active=False)
            
        stripe.product.modify(
        product_id,
        active=False
        )
        try:
            # Delete the product itself
            stripe.Product.delete(product_id)
        except stripe.error.InvalidRequestError as e:
            print(f"Product {product_id} cannot be deleted: {e}")
    return "yes"





if __name__ == '__main__':
    app.run(debug=True,port=5000)
