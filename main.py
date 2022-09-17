from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", "sqlite:///movieTOP.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
Bootstrap(app)
db = SQLAlchemy(app)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(600), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(300), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)


db.create_all()


class RateMovieForm(FlaskForm):
    rating = StringField('Your Rating Out of 10 e.g. 7.5', validators=[DataRequired()])
    review = StringField('Your Review', validators=[DataRequired()])
    submit = SubmitField('Done')


class AddMovieForm(FlaskForm):
    add_movie = StringField('Movie Title', validators=[DataRequired()])
    submit = SubmitField('Add Movie')


API_KEY = os.environ.get('MOVIE_DB_API_KEY')
URL = "https://api.themoviedb.org/3/search/movie"
TMDB_IMAGE_URL = 'https://image.tmdb.org/t/p/w500'


@app.route("/find")
def find_movie():
    title = request.args.get("title")
    year = request.args.get("year").split("-")[0]
    description = request.args.get("description")
    img_url = request.args.get("img_url")
    new_movie = Movie(title=title, year=year,
                      description=description, rating=0,
                      ranking=0, review="None", img_url=f"{TMDB_IMAGE_URL}/{img_url}")
    db.session.add(new_movie)
    db.session.commit()
    return redirect(url_for('edit', title=title))


@app.route("/")
def home():
    all_movies = Movie.query.order_by(Movie.rating.desc()).all()
    for i in range(len(all_movies)):
        all_movies[i].ranking = i % len(all_movies) + 1
        db.session.commit()
    return render_template("index.html", movies=all_movies)


@app.route("/edit", methods=['GET', 'POST'])
def edit():
    form = RateMovieForm()
    if form.validate_on_submit():
        movie_id = request.args.get("id")
        print(movie_id)
        if movie_id:
            movie_to_update = Movie.query.get(movie_id)
        else:
            title = request.args.get("title")
            movie_to_update = Movie.query.filter_by(title=title).first()
        movie_to_update.rating = form.rating.data
        movie_to_update.review = form.review.data
        db.session.commit()

        return redirect(url_for('home'))
    return render_template("edit.html", form=form)


@app.route("/delete")
def delete():
    movie_id = request.args.get("id")
    movie_to_delete = Movie.query.get(movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/add", methods=['GET', 'POST'])
def add_movie():
    form = AddMovieForm()
    if form.validate_on_submit():
        parameters = {
            "api_key": API_KEY,
            "query": form.add_movie.data
        }
        response = requests.get(url=URL, params=parameters)
        data = response.json()
        movies = data['results']
        # print(movies)
        return render_template('select.html', movies=movies)
    return render_template('add.html', form=form)


if __name__ == '__main__':
    app.run(debug=True)
