from flask import Flask, render_template, request, redirect, flash, abort
import pymysql
# classses are capitalized
from dynaconf import Dynaconf
import flask_login

app = Flask(__name__)

conf = Dynaconf(
    settings_file = ["settings.toml"]
)

app.secret_key = conf.secret_key

login_manager = flask_login.LoginManager()
login_manager.init_app(app)
login_manager.login_view = ('/sign_in')


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

class User:
    is_authenticated = True
    is_anonymous = False
    is_active = True

    def __init__(self, id, username, email, first_name, last_name):
        self.id = id
        self.username = username
        self.email = email
        self.first_name = first_name
        self.last_name = last_name

    def get_id(self):
        return str(self.id)

@login_manager.user_loader
def load_user(user_id):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM `Customer` WHERE `id` = {user_id}")

    result = cursor.fetchone()
    #if there is no vaule in the requested database vaule a None will be returned
    cursor.close()
    conn.close()

    if result is not None:
        return User(result["id"], result["username"], result["email"], result["first_name"], result["last_name"])

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
    customer_id = flask_login.current_user.id

    conn = connect_db()

    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM `Product` WHERE `id` = {product_id};")
    # SELECT * refers to all column

    # conn and cursor will be gray and unusable when put after return

    result = cursor.fetchone()

    cursor.execute(f"""
                    SELECT  
                        `Review`.`customer_id`,
                        `Review`.`rating`,
                        `Review`.`timestamp`,
                        `Review`.`comment`,
                        `Review`.`title`,
                        `Customer`.`username` 
                    FROM 
                        Review
                    JOIN 
                        Customer ON `customer_id`= `Customer`.`id`
                    WHERE
                        product_id = {product_id};
                    """)

    reviews = cursor.fetchall()

    cursor.execute(f"SELECT * FROM `Customer` WHERE `id` = {customer_id}")
    customer = cursor.fetchone

    cursor.close()
    conn.close()
    # used to not DDOX the database

    average_rating = 0
    for rating in reviews["rating"]:
        average_rating += float(rating)
    average_rating /= len(reviews["rating"])

    if result is None:
        abort(404)
        #redirect to 404 page
    return render_template("product.html.jinja", product = result, reviews = reviews, customer = customer, product_id = product_id, average_rating = average_rating)
    # if you return with a string the page will just have that string 
    
@app.route("/sign_up", methods=["POST", "GET"])
def sign_up_page():
    if flask_login.current_user.is_authenticated:
        return redirect("/")

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
        if len(password) >= 10:
            if password == confirm_password:
                try:
                    cursor.execute(f"""
                    INSERT INTO `Customer` 
                        ( `username`, `password`, `first_name`, `last_name`, `email`, `phone_number`, `address` )
                    VALUES
                        ( '{username}', '{password}', '{first_name}', '{last_name}', '{email}', '{phone_number}', '{address}' ) ;
                    """)
                    # column names need to be in `ticks`
                except pymysql.err.IntegrityError:
                    flash("Sorry, that username/email is already in use.")
                else:
                    return redirect("/sign_in")
                    #ONLY ONE RETURN WILL BE RUN
                finally:
                    cursor.close()
                    conn.close()
            else:
                flash("Sorry, Password and Confirm Password must match.")
        else:
            flash("Sorry, Your Password need to be stronger: it should be at least 10 characters long")
    return render_template("sign_up.html.jinja")

@app.route("/sign_in", methods=["POST", "GET"])
def sign_in_page():
    if flask_login.current_user.is_authenticated:
        return redirect("/")


    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        
        conn = connect_db()
        cursor = conn.cursor()


        cursor.execute(f"SELECT * FROM `Customer` WHERE `username` = '{username}' ;")
        #there are '' around {username} because its a string

        result = cursor.fetchone()

        if result is None:
            flash("Your username/password is incorrect")

        elif password != result["password"]:
            flash("Your username/password is incorrect")

        else:
            user = User(result["id"], result["username"], result["email"], result["first_name"], result["last_name"])
            flask_login.login_user(user)

            return redirect('/')

        cursor.close()
        conn.close()

    return render_template("sign_in.html.jinja")

@app.route('/logout')
def logout():
    flask_login.logout_user()
    return redirect('/')

#refreshing a form error cause it to send the form again

@app.route("/product/<product_id>/cart", methods = ["POST", "GET"])
@flask_login.login_required
def add_to_cart(product_id):
    quantity = request.form["quantity"]
    customer_id = flask_login.current_user.id
    
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute(f"""
    INSERT INTO `Cart` 
        ( `product_id`, `customer_id`, `quantity` )
    VALUES
        ( '{product_id}', '{customer_id}', '{quantity}' ) 
    ON DUPLICATE KEY UPDATE
        `quantity` = `quantity` + {quantity};
    """)
    
    cursor.close()
    conn.close()
    return redirect("/cart")

@app.route("/cart")
@flask_login.login_required
def cart_page():
    conn = connect_db()
    cursor = conn.cursor()
    customer_id = flask_login.current_user.id
    
    cursor.execute(f"""
        SELECT 
            `name`, 
            `price`, 
            `image`, 
            `Cart`.`id`,
            `quantity`
        FROM `Cart`
        JOIN `Product` ON `product_id` = `Product`.`id`
        WHERE `customer_id` = {customer_id}
    """)
    
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    total_price_py = 0
    for cost in results:
        total_price_py += cost["price"] * cost["quantity"]

    return render_template("cart.html.jinja", cart_products = results, total_price = total_price_py)

@app.route("/cart/<item_id>/del", methods=["POST"])
@flask_login.login_required
def cart_delete(item_id):
    conn = connect_db()
    cursor = conn.cursor()
    customer_id = flask_login.current_user.id

    cursor.execute(f"""
    DELETE FROM Cart 
    WHERE 
    `customer_id` = {customer_id}
    And
    `Cart`.`id` = {item_id}
    ;""")
    
    cursor.close()
    conn.close()
    return redirect("/cart")
# you can use a value on a button to store the id too.

@app.route("/cart/<cart_id>/update", methods=["POST"])
@flask_login.login_required
def cart_update(cart_id):
    conn = connect_db()
    cursor = conn.cursor()
    customer_id = flask_login.current_user.id
    quantity = request.form["quantity"]

    cursor.execute(f"""
        UPDATE Cart
        SET `quantity` = {quantity}
        WHERE     
            `customer_id` = {customer_id}
        And
            `Cart`.`id` = {cart_id}
    ;""")
    
    cursor.close()
    conn.close()
    return redirect("/cart")

@app.route("/sales")
@flask_login.login_required
def sales_page():
    conn = connect_db()
    cursor = conn.cursor()
    customer_id = flask_login.current_user.id
    
    cursor.execute(f"""
        SELECT 
            `name`, 
            `price`, 
            `image`, 
            `Cart`.`id`,
            `quantity`
        FROM `Cart`
        JOIN `Product` ON `product_id` = `Product`.`id`
        WHERE `customer_id` = {customer_id}
    """)
    
    results1 = cursor.fetchall()

    cursor.execute(f"SELECT * FROM `Customer` WHERE `id` = {customer_id};")
    
    results2 = cursor.fetchone()

    cursor.close()
    conn.close()

    subtotal_price_py = 0
    for cost in results1:
        subtotal_price_py += cost["price"] * cost["quantity"]

    discount = 0
    discount_dollar = subtotal_price_py * (discount / 100)

    taxes = 0
    taxes_dollar = (subtotal_price_py + discount_dollar) * (taxes/ 100)

    total = subtotal_price_py + discount_dollar + taxes_dollar


    if len(results1) == 0:
        return redirect("/cart") 
    else:
        return render_template("sales.html.jinja", 
                               cart_products = results1, 
                               subtotal_price_py = subtotal_price_py, 
                               results2 = results2, 
                               discount = discount,
                               taxes = taxes,
                               discount_dollar = discount_dollar,
                               taxes_dollar = taxes_dollar,
                               total = total)

@app.route("/sales/purchase", methods=["POST"])
@flask_login.login_required
def purchase():
    conn = connect_db()
    cursor = conn.cursor()
    customer_id = flask_login.current_user.id

    cursor.execute(f"SELECT * FROM Cart WHERE `customer_id` = {customer_id};")
    cart = cursor.fetchall()

    cursor.execute(f"""
        INSERT INTO Sale 
            (`customer_id`, `status`)
        VALUES 
            ({customer_id}, "ongoing");
    """)
    
    sale_id = cursor.lastrowid

    for purchase in cart:   
        cursor.execute(f"""
            INSERT INTO SaleProduct 
                (`sale_id`, `product_id`, `quantity`)
            VALUES 
                ({sale_id}, {purchase['product_id']}, {purchase['quantity']});
        """)

    cursor.execute(f"DELETE FROM Cart WHERE `customer_id` = {customer_id};")

    cursor.close()
    conn.close()
    return redirect("/thank_you")

@app.route("/thank_you")
@flask_login.login_required
def thank_you_page():
    return render_template("thank_you.html.jinja")

@app.route("/cart/sales")
@flask_login.login_required
def cart_to_sales():
    return redirect("/sales")

@app.route("/sales/<item_id>/update", methods=["POST"])
@flask_login.login_required
def sales_update(item_id):
    conn = connect_db()
    cursor = conn.cursor()
    customer_id = flask_login.current_user.id
    quantity = request.form["quantity"]

    cursor.execute(f"""
        UPDATE Cart
        SET `quantity` = {quantity}
        WHERE     
            `Cart`.`id` = {item_id};
    """)
    
    cursor.close()
    conn.close()
    return redirect("/sales")

@app.route("/sales/address_update", methods=["POST"])
@flask_login.login_required
def address_update():
    conn = connect_db()
    cursor = conn.cursor()
    customer_id = flask_login.current_user.id
    address = request.form["input_address"]

    cursor.execute(f"""
        UPDATE Customer
        SET `address` = '{address}'
        WHERE     
            `Customer`.`id` = {customer_id};
    """)
    
    cursor.close()
    conn.close()
    return redirect("/sales")

@app.route("/product/<product_id>/review", methods=["POST"])
@flask_login.login_required
def review(product_id):
    conn = connect_db()
    cursor = conn.cursor()
    customer_id = flask_login.current_user.id
    review_rating = request.form["review_rating"]
    review_title = request.form["review_title"]
    review_text = request.form["review_text"]

    try:
        cursor.execute(f"""
            INSERT INTO Review 
                (`product_id`, `customer_id`, `rating`, `comment`, `title`)
            VALUES 
                ('{product_id}', '{customer_id}', '{review_rating}', '{review_text}', '{review_title}');
        """)
    except pymysql.err.IntegrityError:
        cursor.execute(f"""
            UPDATE Review
            SET 
                `rating` = '{review_rating}',
                `comment` = '{review_title}',
                `title` = '{review_text}'
            WHERE     
                `product_id` = '{product_id}'
                AND
                `customer_id` = '{customer_id}';
        """)
    else:
        flash("Sorry, something when wrong")
    finally:
        cursor.close()
        conn.close()    
    return redirect(f"/product/{product_id}")
