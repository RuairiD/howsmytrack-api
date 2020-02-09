# How's My Track?
"How's My Track?" is a website built for musicians and music producers to solicit feedback on unfinished tracks. Users submit a request as a Soundcloud URL, and may optionally include information on what they'd like feedback on, or any other context. Once every 24 hours, these requests are assigned to 'groups' of 4. Once assigned to a group, users can listen to the other tracks in their group and leave feedback for their peers. Once a user has written feedback for everyone else in their group, they will be able to see their own feedback. Users can also rate the feedback they receive; users with a higher average rating will be grouped together, incentivising writing constructive, high quality feedback in order to be grouped with other users who write constructive, high quality feedback in future.

The frontend portion of "How's My Track?" can be found [here](https://github.com/ruairid/howsmytrack-web).

## Running
This is a pretty standard Django project for the most part. As-is, it is designed to be run on Heroku, but setting `DEBUG = True` in `settings.py` will allow it to run on `localhost` with a sqlite DB. Run these inside a python3 virtualenv:

 1. `pip install -r requirements.txt # Install dependencies`
 2. `python manage.py migrate # Create database tables`
 3. `python manage.py runserver # Done.`

## API
Almost the entire API is served from a `/graphql` endpoint*; when running in debug mode, visiting `/graphql` in a browser allows access to a playground where the user can dick around with queries. 

\* this was my first GraphQL project; as such, things like schema design are likely a bit crap.

## Authentication
JWTs are used for stateless authentication. The [`django-graphql-jwt`](https://github.com/flavors/django-graphql-jwt) package is used for providing tokens, which are set in a HttpOnly `JWT` cookie. Due to the relative lack of sensitive data stored (essentially email addresses and Soundcloud URLs), authentication wasn't extensively researched or implemented, and functions in pretty simple capacity.

## Scheduled Jobs
A combination of `apscheduler` and `django_apscheduler` are used to run two scheduled jobs.
* `calculate_user_ratings` recalculates the average ratings of all users based on their recent feedback ratings (run at 2:00AM UTC every day)
* `assign_groups` assigns all unassigned feedback requests to new groups (run at 2:30AM UTC every day)
