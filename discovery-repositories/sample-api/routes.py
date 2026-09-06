"""Clearly labelled local source fixture for Docker Git discovery demonstrations."""


@app.get("/demo/users")
def list_users():
    pass


@app.post("/demo/users")
def create_user():
    pass


@app.route("/demo/orders/<id>", methods=["GET", "DELETE"])
def order(id):
    pass
