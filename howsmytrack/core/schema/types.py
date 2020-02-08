import graphene


class FeedbackRequestType(graphene.ObjectType):
    id = graphene.Int()
    media_url = graphene.String()
    media_type = graphene.String()
    feedback_prompt = graphene.String()


class FeedbackResponseType(graphene.ObjectType):
    id = graphene.Int()
    feedback_request = graphene.Field(FeedbackRequestType)
    feedback = graphene.String()
    submitted = graphene.Boolean()
    rating = graphene.Int()


class UserType(graphene.ObjectType):
    username = graphene.String()
    rating = graphene.Float()


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
