from flask import Flask, render_template, request, redirect
import pymysql
# classses are capitalized
from dynaconf import Dynaconf

app = Flask(__name__)

conf = Dynaconf(
    settings_file = ["settings.toml"]
)


def connect_db():
    conn =pymysql.connect(
        host="10.100.34.80",
        database="bwang_streamline_water",
        user='bwang',
        password= conf.password,
        autocommit= True,
        cursorclass= pymysql.cursors.DictCursor
    )

    return conn

#coordinator connect two fuction
@app.route("/")
def index():
    return render_template("homepage.html.jinja")

@app.route("/browse")
def product_browse():
    query = request.args.get("query")

    conn = connect_db()

    cursor = conn.cursor()

    if query is None:
        cursor.execute("SELECT * FROM `Product`;")
    else:
        cursor.execute(f"SELECT * FROM `Product` WHERE `name` LIKE '%{query}%' OR `description` LIKE '%{query}%' OR `ingredients` LIKE '%{query}%';")

    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("browse.html.jinja", products = results)

@app.route("/product/<product_id>")
def product_page(product_id):
    
    conn = connect_db()

    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM `Product` WHERE `id` = {product_id};")
    # SELECT * refers to all column

    # conn and cursor will be gray and unusable when put after return

    result = cursor.fetchone()

    cursor.close()
    conn.close()
    # used to not DDOX the database

    return render_template("product.html.jinja", product = result)
    # if you return with a string the page will just have that string

@app.route("/sign_up", methods=["POST", "GET"])
def sign_up_page():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        email = request.form["email"]
        phone_number = request.form["phone_number"]
        address = request.form["address"]
        #uses [] because its a dict
        #werkzeug error means typo in name

        conn = connect_db()

        cursor = conn.cursor()

        cursor.execute(f"""
        INSERT INTO `Customer` 
            ( `username`, `password`, `first_name`, `last_name`, `email`, `phone_number`, `address` )
        VALUES
            ( '{username}', '{password}', '{first_name}', '{last_name}', '{email}', '{phone_number}', '{address}' ) ;
        """)
        # column names need to be in `ticks`
        
        cursor.close()
        conn.close()
        return redirect("/sign_in")

    return render_template("sign_up.html.jinja")

@app.route("/sign_in")
def sign_in_page():
    
    
    
    
    conn = connect_db()

    cursor = conn.cursor()

    #cursor.execute(f"SELECT * FROM `Product` WHERE `id` = {product_id};")

    cursor.close()
    conn.close()

    return render_template("sign_in.html.jinja")

#refreshing a form error cause it to send the form again