from flask import Flask,render_template,request,redirect,url_for

app = Flask(__name__)


# Home
@app.route("/")
def home():

    return render_template("index.html")



# Login Page
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        print(email, password)
        return redirect(url_for("dashboard"))
    return render_template("login.html")

# Register Page
@app.route("/register",methods=["GET","POST"])
def register():
    if request.method=="POST":
        name=request.form["name"]
        email=request.form["email"]
        password=request.form["password"]
        role=request.form["role"]
        print(name,email,password,role)
        return redirect(url_for("login"))
    return render_template("registretion.html")



# Dashboard
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")



app.run(debug=True)

@app.route("/login",methods=["GET","POST"])
def login():

    if request.method=="POST":

        email=request.form["email"]
        password=request.form["password"]

        print(email,password)

        return redirect(url_for("dashboard"))


    return render_template("login.html")

@app.route("/")
def home():
    return render_template("index.html")