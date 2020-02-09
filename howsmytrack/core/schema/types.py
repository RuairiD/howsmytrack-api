import graphene


class FeedbackRequestType(graphene.ObjectType):
    id = graphene.Int()
    media_url = graphene.String()
    media_type = graphene.String()
    feedback_prompt = graphene.String()

    @classmethod
    def from_model(cls, model):
        return cls(
            id=model.id,
            media_url=model.media_url,
            media_type=model.media_type,
            feedback_prompt=model.feedback_prompt,
        )

    def __hash__(self):
        return hash((
            self.id,
            self.media_url,
            self.media_type,
            self.feedback_prompt,
        ))

    def __eq__(self, other):
        return all([
            self.id == other.id,
            self.media_url == other.media_url,
            self.media_type == other.media_type,
            self.feedback_prompt == other.feedback_prompt,
        ])


class FeedbackResponseType(graphene.ObjectType):
    id = graphene.Int()
    feedback_request = graphene.Field(FeedbackRequestType)
    feedback = graphene.String()
    submitted = graphene.Boolean()
    rating = graphene.Int()

    @classmethod
    def from_model(cls, model):
        return cls(
            id=model.id,
            feedback_request=FeedbackRequestType.from_model(model.feedback_request),
            feedback=model.feedback,
            submitted=model.submitted,
            rating=model.rating,
        )

    def __hash__(self):
        return hash((
            self.id,
            self.feedback_request,
            self.feedback,
            self.submitted,
            self.rating,
        ))

    def __eq__(self, other):
        return all([
            self.id == other.id,
            self.feedback_request == other.feedback_request,
            self.feedback == other.feedback,
            self.submitted == other.submitted,
            self.rating == other.rating,
        ])


class UserType(graphene.ObjectType):
    username = graphene.String()
    rating = graphene.Float()

    def __eq__(self, other):
        return all([
            self.username == other.username,
            self.rating == other.rating,
        ])


class FeedbackGroupType(graphene.ObjectType):
    id = graphene.Int()
    name = graphene.String()
    # The URL submitted by the logged in user.
    media_url = graphene.String()
    media_type = graphene.String()
    # The number of users in the group.
    members = graphene.Int()
    # User's feedback responses for other group member's requests 
    feedback_responses = graphene.List(FeedbackResponseType)
    # Feedback received by the user; only sent once user has completed all feedbackReponses
    user_feedback_responses = graphene.List(FeedbackResponseType)

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

        feedback_responses = set()
        for feedback_request in feedback_requests_for_user:
            for feedback_response in feedback_request.feedback_responses.all():
                if feedback_response.user == feedback_groups_user:
                    feedback_responses.add(
                        FeedbackResponseType.from_model(feedback_response)
                    )

        # If user has responded to all requests, find user's request and get responses
        user_feedback_responses = None
        if all([feedback_response.submitted for feedback_response in feedback_responses]):
            # Only returned submitted responses
            user_feedback_responses = [
                FeedbackResponseType.from_model(feedback_response)
                for feedback_response in user_feedback_request.feedback_responses.filter(
                    submitted=True,
                ).all()
            ]

        return cls(
            id=model.id,
            name=model.name,
            media_url=user_feedback_request.media_url,
            media_type=user_feedback_request.media_type,
            members=model.feedback_requests.count(),
            feedback_responses=list(feedback_responses),
            user_feedback_responses=list(user_feedback_responses),
        )

    def __eq__(self, other):
        return all([
            self.id == other.id,
            self.name == other.name,
            self.media_url == other.media_url,
            self.media_type == other.media_type,
            self.members == other.members,
            self.feedback_responses == other.feedback_responses,
            self.user_feedback_responses == other.user_feedback_responses,
        ])
