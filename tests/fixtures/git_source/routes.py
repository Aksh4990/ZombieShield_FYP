@app.get("/users")
def users():
    pass

@app.post("/users")
def create_user():
    pass

@app.put("/users/{id}")
def update_user():
    pass

@app.route("/orders/<id>", methods=["GET", "POST"])
def orders(id):
    pass
