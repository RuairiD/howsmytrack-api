import graphene


class FeedbackRequestType(graphene.ObjectType):
    id = graphene.Int()
    media_url = graphene.String()
    media_type = graphene.String()
    feedback_prompt = graphene.String()
    email_when_grouped = graphene.Boolean()
    genre = graphene.String()

    @classmethod
    def from_model(cls, model):
        return cls(
            id=model.id,
            media_url=model.media_url,
            media_type=model.media_type,
            feedback_prompt=model.feedback_prompt,
            email_when_grouped=model.email_when_grouped,
            genre=model.genre,
        )

    def __eq__(self, other):
        return all(
            [
                self.id == other.id,
                self.media_url == other.media_url,
                self.media_type == other.media_type,
                self.feedback_prompt == other.feedback_prompt,
                self.email_when_grouped == other.email_when_grouped,
                self.genre == other.genre,
            ]
        )


class FeedbackResponseReplyType(graphene.ObjectType):
    id = graphene.Int()
    # A simplified user identifier i.e. "You" or "Them"
    username = graphene.String()
    text = graphene.String()
    allow_replies = graphene.Boolean()
    time_created = graphene.types.datetime.DateTime()

    @classmethod
    def from_model(cls, model, feedback_groups_user):
        username = "Them"
        if feedback_groups_user == model.user:
            username = "You"

        return cls(
            id=model.id,
            username=username,
            text=model.text,
            allow_replies=model.allow_replies,
            time_created=model.time_created,
        )

    def __eq__(self, other):
        return all(
            [
                self.id == other.id,
                self.username == other.username,
                self.text == other.text,
                self.allow_replies == other.allow_replies,
                self.time_created == other.time_created,
            ]
        )


class FeedbackResponseRepliesType(graphene.ObjectType):
    """A collection of replies for a FeedbackResponse, along with
    pertinent metadata."""

    replies = graphene.List(FeedbackResponseReplyType)
    # Whether or not either of the users has chosen to disable
    # writing additional replies.
    allow_further_replies = graphene.Boolean()

    @classmethod
    def from_feedback_response(cls, feedback_response, feedback_groups_user):
        return cls(
            replies=[
                FeedbackResponseReplyType.from_model(reply, feedback_groups_user)
                for reply in feedback_response.ordered_replies
            ],
            allow_further_replies=feedback_response.allow_replies
            and feedback_response.allow_further_replies,
        )

    def __eq__(self, other):
        return all(
            [
                self.replies == other.replies,
                self.allow_further_replies == other.allow_further_replies,
            ]
        )


class FeedbackResponseType(graphene.ObjectType):
    id = graphene.Int()
    feedback_request = graphene.Field(FeedbackRequestType)
    feedback = graphene.String()
    submitted = graphene.Boolean()
    rating = graphene.Int()
    # Whether or not the original feedback author allowed the other
    # user to reply to this feedback; this is used to decide whether
    # to show the 'View Replies' button on the frontend.
    allow_replies = graphene.Boolean()
    replies = graphene.Int()
    unread_replies = graphene.Int()

    @classmethod
    def from_model(cls, model, feedback_groups_user):
        return cls(
            id=model.id,
            feedback_request=FeedbackRequestType.from_model(model.feedback_request),
            feedback=model.feedback,
            submitted=model.submitted,
            rating=model.rating,
            allow_replies=model.allow_replies,
            replies=model.replies.count(),
            unread_replies=model.replies.exclude(user=feedback_groups_user,)
            .filter(time_read__isnull=True)
            .count(),
        )

    def __eq__(self, other):
        return all(
            [
                self.id == other.id,
                self.feedback_request == other.feedback_request,
                self.feedback == other.feedback,
                self.submitted == other.submitted,
                self.rating == other.rating,
                self.allow_replies == other.allow_replies,
                self.replies == other.replies,
                self.unread_replies == other.unread_replies,
            ]
        )


class UserType(graphene.ObjectType):
    username = graphene.String()
    rating = graphene.Float()
    notifications = graphene.Int()

    send_reminder_emails = graphene.Boolean()

    def __eq__(self, other):
        return all(
            [
                self.username == other.username,
                self.rating == other.rating,
                self.notifications == other.notifications,
                self.send_reminder_emails == other.send_reminder_emails,
            ]
        )


class MediaInfoType(graphene.ObjectType):
    media_url = graphene.String()
    media_type = graphene.String()

    def __eq__(self, other):
        return all(
            [self.media_url == other.media_url, self.media_type == other.media_type,]
        )


class FeedbackGroupType(graphene.ObjectType):
    id = graphene.Int()
    name = graphene.String()
    time_created = graphene.types.datetime.DateTime()
    # The URL submitted by the logged in user.
    media_url = graphene.String()  # TODO deprecate
    media_type = graphene.String()  # TODO deprecate
    # The logged in user's request in this group
    feedback_request = graphene.Field(FeedbackRequestType)
    # The number of users in the group for whom the user must leave feedback.
    members = graphene.Int()
    # The number of users in the group without tracks.
    trackless_members = graphene.Int()
    # User's feedback responses for other group member's requests
    feedback_responses = graphene.List(FeedbackResponseType)
    # Feedback received by the user; only sent once user has completed all feedbackReponses
    user_feedback_responses = graphene.List(FeedbackResponseType)
    # In mosts cases, this is just the same as len(user_feedback_responses); the user case for
    # this field is where the user hasn't completed their feedback yet but we still want to
    # show the user that other people have already completed feedback for them, spurring them on.
    user_feedback_response_count = graphene.Int()

    @classmethod
    def from_model(cls, model, feedback_groups_user):
        user_feedback_request = [
            feedback_request
            for feedback_request in model.feedback_requests.all()
            if feedback_request.user == feedback_groups_user
        ][0]

        feedback_requests_for_user = [
            feedback_request
            for feedback_request in model.feedback_requests.all()
            if feedback_request.user != feedback_groups_user
        ]

        feedback_responses = []
        for feedback_request in feedback_requests_for_user:
            for feedback_response in feedback_request.feedback_responses.all():
                if feedback_response.user == feedback_groups_user:
                    feedback_responses.append(
                        FeedbackResponseType.from_model(
                            feedback_response, feedback_groups_user
                        )
                    )

        # If user has responded to all requests, find user's request and get responses
        submitted_responses_for_user = user_feedback_request.feedback_responses.filter(
            submitted=True,
        ).all()
        user_feedback_responses = None
        if all(
            [feedback_response.submitted for feedback_response in feedback_responses]
        ):
            # Only returned submitted responses
            user_feedback_responses = [
                FeedbackResponseType.from_model(feedback_response, feedback_groups_user)
                for feedback_response in submitted_responses_for_user
            ]

        return cls(
            id=model.id,
            name=model.name,
            time_created=model.time_created,
            media_url=user_feedback_request.media_url,
            media_type=user_feedback_request.media_type,
            feedback_request=FeedbackRequestType.from_model(user_feedback_request),
            members=model.feedback_requests.filter(media_url__isnull=False,)
            .exclude(id=user_feedback_request.id,)
            .count(),
            trackless_members=model.feedback_requests.filter(media_url__isnull=True,)
            .exclude(id=user_feedback_request.id,)
            .count(),
            feedback_responses=feedback_responses,
            user_feedback_responses=user_feedback_responses,
            user_feedback_response_count=len(submitted_responses_for_user),
        )

    def __eq__(self, other):
        return all(
            [
                self.id == other.id,
                self.name == other.name,
                self.time_created == other.time_created,
                self.media_url == other.media_url,
                self.media_type == other.media_type,
                self.members == other.members,
                self.trackless_members == other.trackless_members,
                self.feedback_responses == other.feedback_responses,
                self.user_feedback_responses == other.user_feedback_responses,
                self.user_feedback_response_count == other.user_feedback_response_count,
            ]
        )
