from flask import Flask, render_template, request
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