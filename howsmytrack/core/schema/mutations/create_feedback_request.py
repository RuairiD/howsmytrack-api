import graphene
from django.core.exceptions import ValidationError

from howsmytrack.core.models import FeedbackGroupsUser
from howsmytrack.core.models import FeedbackRequest
from howsmytrack.core.validators import validate_media_url


class CreateFeedbackRequest(graphene.Mutation):
    class Arguments:
        media_url = graphene.String(required=False)
        genre = graphene.String(required=False)
        email_when_grouped = graphene.Boolean(required=False)
        feedback_prompt = graphene.String(required=False)

    success = graphene.Boolean()
    error = graphene.String()
    invalid_media_url = graphene.Boolean()

    def __eq__(self, other):
        return all([self.success == other.success, self.error == other.error,])

    def mutate(
        self,
        info,
        media_url=None,
        genre=None,
        email_when_grouped=False,
        feedback_prompt=None,
    ):
        user = info.context.user
        if user.is_anonymous:
            return CreateFeedbackRequest(
                success=False, error="Not logged in.", invalid_media_url=False,
            )

        feedback_groups_user = FeedbackGroupsUser.objects.filter(user=user,).first()

        # Validate the media url, if one exists.
        media_type = None
        if media_url:
            try:
                media_type = validate_media_url(media_url)
            except ValidationError as e:
                return CreateFeedbackRequest(
                    success=False, error=e.message, invalid_media_url=True,
                )

        # Only create a new request if the user has an outstanding, ungrouped request
        # (should only happen if user's request is from within the last 24 hours or
        # the request is the only one submitted :cry: )
        unassigned_requests = FeedbackRequest.objects.filter(
            user=feedback_groups_user, feedback_group=None,
        ).count()
        if unassigned_requests > 0:
            return CreateFeedbackRequest(
                success=False,
                error="You have an unassigned feedback request. Once that request has been assigned to a feedback group, you will be eligible to submit another request.",
                invalid_media_url=False,
            )

        # Reject requests for the same URL (if the other submission hasn't been grouped yet)
        # This prevents users creating multiple accounts to request the same track.
        if media_url:
            existing_track_requests = FeedbackRequest.objects.filter(
                media_url=media_url, feedback_group=None,
            ).count()
            if existing_track_requests > 0:
                return CreateFeedbackRequest(
                    success=False,
                    error="A request for this track is already pending.",
                    invalid_media_url=False,
                )

        feedback_request = FeedbackRequest(
            user=feedback_groups_user,
            media_url=media_url,
            media_type=media_type,
            feedback_prompt=feedback_prompt,
            email_when_grouped=email_when_grouped,
            genre=genre,
        )
        feedback_request.save()

        return CreateFeedbackRequest(success=True, error=None, invalid_media_url=False,)
