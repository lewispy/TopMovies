from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DecimalField
from wtforms.validators import DataRequired
import requests
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)


# CREATE DB
class Base(DeclarativeBase):
    pass


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)


class RateMoviesForm(FlaskForm):
    new_rating = DecimalField(
        'Your Rating out of 10 (e.g. 7.5)',
        places=1,
        validators=[DataRequired(message="Please enter a rating")]
    )
    your_review = StringField(
        'Your Review',
    )
    submit_button = SubmitField('Done')


class AddMovieForm(FlaskForm):
    new_movie = StringField(
        'Movie title'
    )
    add_button = SubmitField("Add Movie")


# CREATE TABLE
class Movie(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=True)
    ranking: Mapped[int] = mapped_column(Integer, nullable=True)
    review: Mapped[str] = mapped_column(String(250), nullable=True)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)


with app.app_context():
    db.create_all()


@app.route("/")
def home():
    result = db.session.execute(db.select(Movie).order_by(Movie.rating))
    all_movies = result.scalars().all()
    for i, movie in enumerate(all_movies):
        all_movies[i].ranking = len(all_movies)-i
    db.session.commit()
    return render_template("index.html", movies=all_movies)


@app.route("/edit", methods=["POST", "GET"])
def edit():
    form = RateMoviesForm()
    movie_id = request.args.get("ID")
    movie_to_update = db.get_or_404(Movie, movie_id)
    movie_title = movie_to_update.title
    if form.validate_on_submit():
        movie_to_update.rating = float(form.new_rating.data)
        movie_to_update.review = form.your_review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", form=form, title=movie_title)


@app.route("/delete")
def delete_movie():
    movie_id = request.args.get("ID")
    movie_to_delete = db.get_or_404(Movie, movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/add", methods=["GET", "POST"])
def add_movie():
    form = AddMovieForm()
    my_key = os.getenv("THE_MOVIE_DB_KEY")
    if request.method == "POST":
        if form.validate_on_submit():
            movie_title = form.new_movie.data
            search_url = "https://api.themoviedb.org/3/search/movie"
            response = requests.get(url=search_url, params={"api_key":my_key, "query":movie_title})
            data = response.json()["results"]
            return render_template("select.html", options=data)
    else:
        movie_id = request.args.get("ID")
        if movie_id:
            details_url = f"https://api.themoviedb.org/3/movie/{movie_id}"
            image_url = "https://image.tmdb.org/t/p/w500"
            response = requests.get(url=details_url, params={"api_key":my_key})
            data = response.json()
            print(data)
            new_movie = Movie(
                title=data["title"],
                year=data["release_date"].split("-")[0],
                description=data["overview"],
                img_url=f"{image_url}{data['poster_path']}"
            )
            print(f"{image_url}{data['poster_path']}")
            with app.app_context():
                db.session.add(new_movie)
                db.session.commit()
            movie_to_read = db.session.execute(db.select(Movie).where(Movie.title == data["title"])).scalar()
            return redirect(url_for("edit", ID=movie_to_read.id))
        else:
            print("Movie id not found!")

    return render_template("add.html", form=form)


if __name__ == '__main__':
    app.run(debug=True)
