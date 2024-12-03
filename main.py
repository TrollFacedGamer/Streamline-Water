from flask import Flask, render_template

app = Flask(__name__)

#coordinator connect two fuction
@app.route("/")
def index():
    return render_template("homepage.html.jinja")