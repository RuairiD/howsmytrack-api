import graphene
from django.core.exceptions import ValidationError

from howsmytrack.core.models import FeedbackGroupsUser
from howsmytrack.core.models import FeedbackRequest
from howsmytrack.core.validators import validate_media_url


class EditFeedbackRequest(graphene.Mutation):

    class Arguments:
        feedback_request_id = graphene.Int(required=True)
        email_when_grouped = graphene.Boolean(required=False)
        media_url = graphene.String(required=False)
        feedback_prompt = graphene.String(required=False)
        genre = graphene.String(required=False)

    success = graphene.Boolean()
    error = graphene.String()
    invalid_media_url = graphene.Boolean()

    def __eq__(self, other):
        return all([
            self.success == other.success,
            self.error == other.error,
        ])

    def mutate(self, info, feedback_request_id, email_when_grouped=None, media_url=None, feedback_prompt=None, genre=None):
        user = info.context.user
        if user.is_anonymous:
            return EditFeedbackRequest(
                success=False,
                error='Not logged in.',
                invalid_media_url=False,
            )

        feedback_groups_user = FeedbackGroupsUser.objects.filter(
            user=user,
        ).first()

        # Validate the media url
        media_type = None
        if media_url:
            try:
                media_type = validate_media_url(media_url)
            except ValidationError as e:
                return EditFeedbackRequest(
                    success=False,
                    error=e.message,
                    invalid_media_url=True,
                )

        # Reject the edit if the user does not own the request (or if it doesn't exist)
        feedback_request = FeedbackRequest.objects.filter(
            user=feedback_groups_user,
            id=feedback_request_id,
        ).first()
        if not feedback_request:
            return EditFeedbackRequest(
                success=False,
                error='You are not the owner of this feedback request.',
                invalid_media_url=False,
            )

        # Reject the edit if the request has already been assigned to a group.
        if feedback_request.feedback_group:
            return EditFeedbackRequest(
                success=False,
                error='This request has already been assigned to a feedback group and cannot be edited.',
                invalid_media_url=False,
            )

        feedback_request.media_url = media_url
        feedback_request.media_type = media_type
        # Allow empty feedback prompt
        if feedback_prompt is not None:
            feedback_request.feedback_prompt = feedback_prompt
        if email_when_grouped is not None:
            feedback_request.email_when_grouped = email_when_grouped
        if genre is not None:
            feedback_request.genre = genre

        feedback_request.save()

        return EditFeedbackRequest(
            success=True,
            error=None,
            invalid_media_url=False,
        )
