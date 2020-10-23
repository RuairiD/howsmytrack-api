# How's My Track? (API)
[![Build Status](https://travis-ci.org/RuairiD/howsmytrack-api.svg?branch=master)](https://travis-ci.org/RuairiD/howsmytrack-api)[![Coverage Status](https://coveralls.io/repos/github/RuairiD/howsmytrack-api/badge.svg?branch=master)](https://coveralls.io/github/RuairiD/howsmytrack-api?branch=master)

"How's My Track?" is a website built for musicians and music producers to solicit feedback on unfinished tracks. Users submit a request as a Soundcloud URL, and may optionally include information on what they'd like feedback on, or any other context. Once every 24 hours, these requests are assigned to 'groups' of 4. Once assigned to a group, users can listen to the other tracks in their group and leave feedback for their peers. Once a user has written feedback for everyone else in their group, they will be able to see their own feedback. Users can also rate the feedback they receive; users with a higher average rating will be grouped together, incentivising writing constructive, high quality feedback in order to be grouped with other users who write constructive, high quality feedback in future.

The frontend portion of "How's My Track?" can be found [here](https://github.com/ruairid/howsmytrack-web).

## Running
This is a pretty standard Django project for the most part. As-is, it is designed to be run on Heroku, but setting `RUNNING_LOCALLY = True` in `settings.py` will allow it to run on `localhost` with a sqlite DB. Run these inside a python3 virtualenv:

 1. `pip install -r requirements.txt`
 2. `pre-commit install`
 3. `python manage.py migrate`
 4. `python manage.py runserver`

## API
Almost the entire API is served from a `/graphql` endpoint*; when running in debug mode, visiting `/graphql` in a browser allows access to a playground where the user can dick around with queries.

\* this was my first GraphQL project; as such, things like schema design are likely a bit crap.

## Authentication
JWTs are used for stateless authentication. The [`django-graphql-jwt`](https://github.com/flavors/django-graphql-jwt) package is used for providing tokens, which are set in a HttpOnly `JWT` cookie. Due to the relative lack of sensitive data stored (essentially email addresses and Soundcloud URLs), authentication wasn't extensively researched or implemented, and functions in pretty simple capacity.

## Scheduled Jobs
A combination of `apscheduler` and `django_apscheduler` are used to run two scheduled jobs.
* `calculate_user_ratings` recalculates the average ratings of all users based on their recent feedback ratings (run at 2:00AM UTC every day)
* `send_group_reminder_emails` sends emails to all users with unsubmitted feedback responses for groups more than 20 hours old (run at 2:15AM UTC every day)
* `assign_groups` assigns all unassigned feedback requests to new groups (run at 2:30AM UTC every day)

## SMTP/Email
A Sendgrid SMTP is used in production to send emails. For development, emails are 'sent' to a local directory using `filebased.EmailBackend`.
