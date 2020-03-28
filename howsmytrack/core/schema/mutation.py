import graphene

from howsmytrack.core.schema.mutations.add_feedback_response_reply import AddFeedbackResponseReply
from howsmytrack.core.schema.mutations.create_feedback_request import CreateFeedbackRequest
from howsmytrack.core.schema.mutations.delete_feedback_request import DeleteFeedbackRequest
from howsmytrack.core.schema.mutations.edit_feedback_request import EditFeedbackRequest
from howsmytrack.core.schema.mutations.mark_replies_as_read import MarkRepliesAsRead
from howsmytrack.core.schema.mutations.obtain_json_web_token_case_insensitive import ObtainJSONWebTokenCaseInsensitive
from howsmytrack.core.schema.mutations.rate_feedback_response import RateFeedbackResponse
from howsmytrack.core.schema.mutations.refresh_token_from_cookie import RefreshTokenFromCookie
from howsmytrack.core.schema.mutations.register_user import RegisterUser
from howsmytrack.core.schema.mutations.submit_feedback_response import SubmitFeedbackResponse
from howsmytrack.core.schema.mutations.update_email import UpdateEmail
from howsmytrack.core.schema.mutations.update_send_reminder_emails import UpdateSendReminderEmails


class Mutation(graphene.ObjectType):
    register_user = RegisterUser.Field()
    update_email = UpdateEmail.Field()
    update_send_reminder_emails = UpdateSendReminderEmails.Field()

    create_feedback_request = CreateFeedbackRequest.Field()
    delete_feedback_request = DeleteFeedbackRequest.Field()
    edit_feedback_request = EditFeedbackRequest.Field()
    submit_feedback_response = SubmitFeedbackResponse.Field()
    rate_feedback_response = RateFeedbackResponse.Field()
    add_feedback_response_reply = AddFeedbackResponseReply.Field()
    mark_replies_as_read = MarkRepliesAsRead.Field()

    token_auth = ObtainJSONWebTokenCaseInsensitive.Field()
    refresh_token_from_cookie = RefreshTokenFromCookie.Field()
