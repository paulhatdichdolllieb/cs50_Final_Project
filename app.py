# test 654321a!
import os

import datetime
from cs50 import SQL
from flask import (
    Flask,
    redirect,
    render_template,
    request,
    session,
    jsonify,
    make_response,
)
from flask_session import Session
from werkzeug.utils import secure_filename


from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required

from tokens import generate_confirmation_token, confirm_token

from PIL import Image, ExifTags

import logging

# setting up the fileupload
UPLOAD_FOLDER = "static/profilepictures"
ALLOWED_EXTENSIONS = {"png", "jpg"}

# configure the application
app = Flask(__name__)

# congigur session to with filters
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
# limet the filesize to 1mb
app.config["MAX_CONTENT_LENGTH"] = 3 * 1024 * 1024
Session(app)

# configurate cs50 SQL
db = SQL("sqlite:///app.db")

# Set the path for the profilepictures
pb_path = "static/profilepictures/"

# supress errors because exif can not get image data
logging.getLogger("PIL.TiffImagePlugin").setLevel(51)


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.errorhandler(413)
def file_to_large(e):
    return render_template(
        "settings.html", user=session["info"], error="filesize needs to be unser 3mb"
    )


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        data = request.form.get("image")

        # check if the post request has the file part

        return render_template("index.html", user=session["info"], data=data)
    else:
        return render_template("index.html", user=session["info"])


@app.route("/poste", methods=["GET", "POST"])
@login_required
def poste():
    if request.method == "POST":
        # check if the text was written/given

        if not request.form.get("poste_text"):
            return redirect("/poste")

        if not request.form.get("visibility"):
            return redirect("/poste")

        title = request.form.get("poste-title")[0:29]

        text = request.form.get("poste_text")[0:15000]

        db.execute(
            "UPDATE user_info SET blogs_int = ? WHERE user_id = ?",
            session["info"]["blogs_int"] + 1,
            session["user_id"],
        )

        update_info()

        db.execute(
            "INSERT INTO postes (title, posted_on, poste, private, user_id) VALUES(?,?,?,?,?)",
            title,
            datetime.datetime.now().strftime("%y/%m/%d %H:%M"),
            text,
            request.form.get("visibility"),
            session["user_id"],
        )

        return redirect("/profile/" + session["info"]["username"])
    else:
        return render_template("poste.html", user=session["info"])


@app.route("/profile/<profile_user>", methods=["GET", "POST"])
@login_required
def profile(profile_user):
    # check if the requestet user does exist
    if not db.execute(
        "SELECT user_id FROM user_info WHERE username = (?)", profile_user
    ):
        return redirect("/")

    # get the looked up profile
    profile_lookup = db.execute(
        "SELECT * FROM user_info WHERE username = (?)", profile_user
    )[0]

    # set the img path

    profile_lookup["profile_picture"] = pb_path + profile_lookup["profile_picture"]

    # chech if the current user wants to visit his own profile or vistit a strangers

    # if it is his own
    if session["user_id"] == profile_lookup["user_id"]:
        # check the requesttype

        if request.method == "POST":
            return render_template("profile.html", user=session["info"])

        else:
            # if its get load the past posts of the user:
            posts = db.execute(
                "SELECT * FROM postes WHERE user_id = ? ORDER BY id DESC ",
                session["user_id"],
            )

            # check if the user has posts
            if not posts:
                return render_template(
                    "profile.html",
                    no_posts="U have not posted sofar",
                    user=session["info"],
                )

            # render the site with posts
            return render_template(
                "profile.html",
                posts=posts,
                user=session["info"],
            )
    else:
        # the user wants to view a strangers profile

        # check if the users are friends by: looking up if there is a friends entrey
        friends = db.execute(
            "SELECT * FROM friends WHERE users_id = ? AND follows = ?",
            session["user_id"],
            profile_lookup["user_id"],
        )

        # if they are not friends or they dont follow eachother
        if not friends or friends[0]["followed_back"] != 1:
            # sekect thr public postes of the user

            posts = db.execute(
                "SELECT * FROM postes WHERE user_id = ? AND private = 'public' ORDER BY id DESC ",
                profile_lookup["user_id"],
            )

            # render the profile
            return render_template(
                "view_profile.html",
                person_info=profile_lookup,
                posts=posts,
                user=session["info"],
            )

        else:
            # if they are friends select all posts that are not privat
            posts = db.execute(
                "SELECT * FROM postes WHERE user_id = ? AND WHERE NOT private = 'private' ORDER BY id DESC ",
                profile_lookup["user_id"],
            )[0]
            # display the profile
            return render_template(
                "view_profile.html",
                person_info=profile_lookup,
                posts=posts,
                user=session["info"],
            )


@app.route("/edit/<post_id>", methods=["GET", "POST"])
@login_required
def edit(post_id):
    if request.method == "POST":
        # check if the text was written/given
        if not request.form.get("poste_text"):
            return redirect("/poste")
        # makes shure private/public or friends was given
        if not request.form.get("visibility"):
            return redirect("/poste")

        # if the user wats to delete the post
        if request.form.get("delete") == "delete":
            # remove the post from the db
            db.execute("DELETE FROM postes WHERE id = ?", post_id)
            # decrease th eamount of posts the user has made by 1
            db.execute(
                "UPDATE user_info SET blogs_int = ? WHERE user_id = ?",
                session["info"]["blogs_int"] - 1,
                session["user_id"],
            )

            update_info()

        else:
            # update the edited post
            title = request.form.get("poste-title")[0:29]

            text = request.form.get("poste_text")[0:15000]

            # check if the post was made by the user who trys to edit it
            if db.execute(
                "SELECT * FROM postes WHERE id  = ? AND user_id = ?",
                post_id,
                session["user_id"],
            ):
                # update the post
                db.execute(
                    "UPDATE postes SET title = ?, posted_on = ?, poste = ?, private = ? WHERE id = ?",
                    title,
                    datetime.datetime.now().strftime("%y/%m/%d %H:%M"),
                    text,
                    request.form.get("visibility"),
                    post_id,
                )
        # rediredt to the currents users profile
        return redirect("../profile/" + session["info"]["username"])
    else:
        # check if the post exists and if it is from the current user
        if not post_id:
            return redirect("/")

        # load th post witch should be edited making shure its from the user
        post = db.execute(
            "SELECT * FROM postes WHERE id  = ? AND user_id = ?",
            post_id,
            session["user_id"],
        )

        if not post:
            return redirect("/")
        else:
            return render_template("edit.html", user=session["info"], post=post)


@app.route("/search", methods=["GET"])
@login_required
def search():
    if request.args and request.args.get("search") is not None:
        search = request.args.get("search")

        results_list = make_search(search)

        if not results_list["followed"] and not results_list["not_followed"]:
            return render_template(
                "search.html",
                user=session["info"],
                no_result="The search has no result, maybe try another spelling",
                search=search,
            )

        return render_template(
            "search.html",
            user=session["info"],
            results_search=results_list,
            search=search,
        )
    else:
        results_list = make_default_search()

        return render_template(
            "search.html", user=session["info"], results_search=results_list
        )


@app.route("/laod_search", methods=["GET"])
@login_required
def load_search():
    if request.args:
        search = request.args.get("c")

        if search == "":
            result = make_default_search()

            res = make_response(jsonify(result))
        else:
            results_list = make_search(search)

            if not results_list["followed"] and not results_list["not_followed"]:
                res = make_response(jsonify({"no_results" : "a"}), 200)
            else:
                res = make_response(jsonify(results_list), 200)
                print("a")

            print(res)

        return res


@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        # check if the user wants to delete his account (finaly)
        if request.form.get("delete_acc") == "delete_acc":
            # delete the account and login
            db.execute("DELETE FROM user_info WHERE user_id = ?", session["user_id"])

            db.execute("DELETE FROM users WHERE id = ?", session["user_id"])

            # delete thhe posts
            db.execute("DELETE FROM postes WHERE user_id = ?", session["user_id"])

            #!! implement later (decrease friend_count)

            # delete from firends
            db.execute("DELETE FROM friends WHERE users_id = ?", session["user_id"])

            session.clear()

            return redirect("/")

        if request.form.get("delete_picture") == "delete_picture":
            # user wants to delete the current profilepicture >> back to default
            # set picture to default
            db.execute(
                "UPDATE user_info SET profile_picture = ? WHERE user_id = ?",
                "default.png",
                session["user_id"],
            )

            path = os.path.join(
                app.config["UPLOAD_FOLDER"], session["info"]["username"] + ".png"
            )

            # delete the current picture from db after checking for existence

            if os.path.exists(path):
                os.remove(path)

            update_info()
        else:
            # check if the post request has the file part
            if "profile_picture" in request.files:
                file = request.files["profile_picture"]
                # if user does not select file, browser also
                # submit an empty part without filename
                if not file.filename == "":
                    # check if file exists and if the extention is wanted
                    if file and allowed_file(file.filename):
                        # save the file as png
                        try:
                            file.save(
                                os.path.join(
                                    app.config["UPLOAD_FOLDER"],
                                    session["info"]["username"] + ".png",
                                )
                            )
                            # rezise image
                            image = Image.open(
                                pb_path + session["info"]["username"] + ".png"
                            )

                            # negate the reset of rotation by the rezise operation

                            # Size of img in pixel
                            width, height = image.size

                            # croping the image to an square to keep the aspectratio
                            new_width, new_height, top, bottom, left, right = (
                                400,
                                400,
                                400,
                                400,
                                400,
                                400,
                            )

                            # check for the smaller variabe
                            if width >= height:
                                new_width = height

                                # use the shorter side as limet and crop the  picture to a sqare
                                top = 0
                                bottom = height
                                left = (width - new_width) / 2
                                right = width - left
                            else:
                                new_height = width

                                top = (height - new_height) / 2
                                bottom = height - top
                                left = 0
                                right = width

                            image_croped = image.crop((left, top, right, bottom))

                            # get oriantation exif tag of the picture
                            for orientation in ExifTags.TAGS.keys():
                                if ExifTags.TAGS[orientation] == "Orientation":
                                    break

                            # get the current rotation
                            image_exif = image._getexif()

                            # rezising the image (loosing rotaion)
                            image_resized = image_croped.resize((400, 400))

                            # rotation the rezised image using the now lost exif data
                            if image_exif is not None:
                                if (
                                    image_exif[orientation] == 3
                                    or image_exif[orientation] == 4
                                ):
                                    image_resized = image_resized.rotate(
                                        180, expand=True
                                    )
                                elif (
                                    image_exif[orientation] == 5
                                    or image_exif[orientation] == 6
                                ):
                                    image_resized = image_resized.rotate(
                                        270, expand=True
                                    )
                                elif (
                                    image_exif[orientation] == 7
                                    or image_exif[orientation] == 8
                                ):
                                    image_resized = image_resized.rotate(
                                        270, expand=True
                                    )

                            # saving the image
                            image_resized.save(
                                os.path.join(
                                    app.config["UPLOAD_FOLDER"],
                                    session["info"]["username"] + ".png",
                                )
                            )
                            # set the fileroute
                            db.execute(
                                "UPDATE user_info SET profile_picture = ? WHERE user_id = ?",
                                session["info"]["username"] + ".png",
                                session["user_id"],
                            )
                        except (AttributeError, KeyError, IndexError):
                            # cases: image don't have getexif
                            pass

        # check if username was given
        if request.form.get("username"):
            username = request.form.get("username")

            if username != "":
                # check if it has been changed and is free to user
                if username != session["info"]["username"] and not db.execute(
                    "SELECT * FROM users WHERE username = ?",
                    request.form.get("username"),
                ):
                    # set the new username
                    db.execute(
                        "UPDATE user_info SET username = ? WHERE user_id = ?",
                        username,
                        session["user_id"],
                    )
                    db.execute(
                        "UPDATE users SET username = ? WHERE id = ?",
                        username,
                        session["user_id"],
                    )

        # check if the colors were given
        if (
            not request.form.get("col_private")
            or not request.form.get("col_public")
            or not request.form.get("col_friends")
            or not request.form.get("text_col_private")
            or not request.form.get("text_col_public")
            or not request.form.get("text_col_friends")
        ):
            return redirect("/2")

        if not request.form.get("username"):
            return redirect("/1")
        # update the choise of colores from the user
        db.execute(
            "UPDATE user_info SET color_private = ?, color_public = ?, color_friends = ?, text_color_private = ?, text_color_friends = ?, text_color_public = ? WHERE user_id = ?",
            request.form.get("col_private"),
            request.form.get("col_public"),
            request.form.get("col_friends"),
            request.form.get("text_col_private"),
            request.form.get("text_col_friends"),
            request.form.get("text_col_public"),
            session["user_id"],
        )

        update_info()

        return redirect("/profile/" + session["info"]["username"])
    else:
        return render_template("settings.html", user=session["info"])


@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "POST":
        # check username in request
        if not request.form.get("username"):
            return render_template("login.html")

        # check password in request
        elif not request.form.get("password"):
            return render_template("login.html")

        # make a user session
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?",
            request.form.get("username").rstrip(),
        )

        if len(rows) != 1:
            return render_template("login.html", error="user does not exist")

        if not check_password_hash(
            rows[0]["hash"], request.form.get("password").rstrip()
        ):
            return render_template(
                "login.html", error="Username and Password do not match"
            )

        # create session
        session["user_id"] = rows[0]["id"]

        # make shure that the amount of blogs is set right

        db.execute(
            "UPDATE user_info SET blogs_int = ? WHERE user_id = ?",
            len(
                db.execute(
                    "SELECT id FROM postes WHERE user_id = ?", session["user_id"]
                )
            ),
            session["user_id"],
        )

        update_info()

        # redirect to hompage
        return redirect("/")

    else:
        return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        if not request.form.get("email"):
            return render_template("register.html")

        elif not request.form.get("username"):
            return render_template("register.html")

        elif not request.form.get("password"):
            return render_template("register.html")

        elif not request.form.get("confirmation"):
            return render_template("register.html")

        # check if uername is still free

        if db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        ):
            return render_template("register.html", error="Username is not available")

        if request.form.get("password") != request.form.get("confirmation"):
            return render_template("register.html", error="Passwords dont match")

        password = request.form.get("password")
        # chasks if it has atleast 8 caracters
        if len(password) < 8:
            return render_template(
                "register.html", error="Password needs to have atlast 8 caracters"
            )
            # cheks if it contains a number
        valid = False

        for i in password:
            if i.isnumeric():
                valid = True

        if not valid:
            return render_template(
                "register.html", error="Password has to contain a number"
            )
        # checks if it contains symbols
        valid1 = False

        for i in password:
            if not i.isalnum():
                valid1 = True
        if not valid1:
            return render_template(
                "register.html", error="Password has to contain a symbol"
            )

        # checking the used email adress
        email = request.form.get("email")

        # token = generate_confirmation_token(email)

        username = request.form.get("username")

        # add new accout to the database

        db.execute(
            "INSERT INTO users (email, username, hash, confirmed, confirmed_on) VALUES(?, ?, ?, ?, ?)",
            email,
            username,
            generate_password_hash(request.form.get("password")),
            int(0),
            int(0),
        )

        # get the users id
        user_id = db.execute("SELECT id FROM users WHERE username = ?", username)[0][
            "id"
        ]

        # store the user_info
        db.execute(
            "INSERT INTO user_info (user_id, username, profile_picture) VALUES(?,?,?)",
            user_id,
            username,
            "default.png",
        )

        # create valid session
        session["user_id"] = user_id
        # update user info
        update_info()
        # redirect to home (logedin)
        return redirect("/")
    else:
        return render_template("register.html")


def update_info():
    # load the profilepicture of the user aswell as his other settings:
    person_info = db.execute(
        "SELECT * FROM user_info WHERE user_id = ?", session["user_id"]
    )[0]

    # set the path to the picture
    person_info["profile_picture"] = pb_path + person_info["profile_picture"]

    session["info"] = person_info


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def make_search(search):
    results_dic = {}

    search_promt = search + "%"

    results_follows = db.execute(
        " SELECT username, blogs_int, profile_picture FROM user_info WHERE username IN (SELECT follows FROM friends WHERE user_id = ?) AND username IN (SELECT username from user_info WHERE username LIKE ?)",
        session["user_id"],
        search_promt,
    )

    results_dic["followed"] = results_follows

    number_rest = 15 - len(results_follows)

    results_normal = db.execute(
        "SELECT username, blogs_int, profile_picture from user_info WHERE username LIKE ? LIMIT ?",
        search_promt,
        number_rest,
    )

    for n in range(len(results_normal)):
        if results_normal[n]["username"] == session["info"]["username"]:
            del results_normal[n]
            break

    results_dic["not_followed"] = results_normal

    if not results_dic:
        results_dic = {}

    return results_dic


def make_default_search():
    results_dic = {}

    already_follows = db.execute(
        "SELECT username, blogs_int, profile_picture from user_info WHERE user_id IN (SELECT follows from friends WHERE user_id = ? LIMIT 10)",
        session["user_id"],
    )

    results_dic["follows"] = already_follows

    number_rest = 16 - len(already_follows)

    no_follower = db.execute(
        "SELECT username, blogs_int, profile_picture FROM user_info ORDER BY blogs_int DESC LIMIT  ?",
        number_rest,
    )

    for n in range(len(no_follower)):
        if no_follower[n]["username"] == session["info"]["username"]:
            del no_follower[n]
            break

    results_dic["not_followed"] = no_follower

    return results_dic
